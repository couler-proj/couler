# Copyright 2020 The Couler Authors. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import inspect
import os
import re
import textwrap

from couler.core.constants import ImagePullPolicy


def argo_safe_name(name):
    """Some names are to be used in the Argo YAML file. For example,
    the generateName and template name in
    https://github.com/argoproj/argo/blob/master/examples/hello-world.yaml. As
    Argo is to use the YAML as part of Kubernetes job description
    YAML, these names must follow Kubernetes's convention -- no
    period or underscore. This function replaces these prohibited
    characters into dashes.
    """
    if name is None:
        return None
    # '_' and '.' are not allowed
    return re.sub(r"_|\.", "-", name)


def invocation_location():
    """If a function A in file B calls function C, which in turn calls
    invocation_location(), the call returns information about the invocation,
    in particular, the caller's name "A" and the line number where A
    calls C. Return (B + line_number) as function_name if A doesn't exist,
    where users directly calls C in file B.

    :return: a tuple of (function_name, invocation_line)
    """
    stack = inspect.stack()
    if len(stack) < 4:
        line_number = stack[len(stack) - 1][2]
        func_name = "%s-%d" % (
            argo_safe_name(workflow_filename()),
            line_number,
        )
    else:
        func_name = argo_safe_name(stack[2][3])
        line_number = stack[3][2]
    return func_name, line_number


def body(func_obj):
    """If a function A calls body(), the call returns the Python source code of
    the function definition body (not including the signature) of A.
    """
    if func_obj is None:
        return None
    code = inspect.getsource(func_obj)
    # Remove function signature
    code = code[code.find(":") + 1 :]  # noqa: E203
    # Function might be defined in some indented scope
    # (e.g. in another function).
    # We need to handle this and properly dedent the function source code
    return textwrap.dedent(code)


def workflow_filename():
    """Return the Python file that defines the workflow.
    """
    stacks = inspect.stack()
    frame = inspect.stack()[len(stacks) - 1]
    full_path = frame[0].f_code.co_filename
    filename, _ = os.path.splitext(os.path.basename(full_path))
    filename = argo_safe_name(filename)
    return filename


def input_parameter_name(name, var_pos):
    """Generate parameter name for using as template input parameter names
    in Argo YAML.  For example, the parameter name "message" in the
    container template print-message in
    https://github.com/argoproj/argo/tree/master/examples#output-parameters.
    """
    return "para-%s-%s" % (name, var_pos)


def container_output(step_name, template_name, output):
    """Generate output name from an Argo container template.  For example,
    "{{steps.generate-parameter.outputs.parameters.hello-param}}" used in
    https://github.com/argoproj/argo/tree/master/examples#output-parameters.
    Each element of return for run_container is contacted by:
    couler.step_name.template_name.output.parameters.output_id
    """
    from couler.core.templates import (
        OutputParameter,
        OutputArtifact,
        OutputEmpty,
    )

    rets = []
    if output is None:
        ret = "couler.%s.%s.outputs.parameters.%s" % (
            step_name,
            template_name,
            "1",
        )
        rets.append(OutputEmpty(value=ret))
        return rets

    output_is_parameter = True
    if "parameters" in output:
        _outputs = output["parameters"]
    elif "artifacts" in output:
        _outputs = output["artifacts"]
        output_is_parameter = False

    if isinstance(_outputs, str):
        _outputs = [_outputs]

    if isinstance(_outputs, list):
        for o in _outputs:
            output_id = o["name"]
            is_global = "globalName" in o
            if output_is_parameter:
                if is_global:
                    ret = "couler.workflow.outputs.parameters.%s" % output_id
                else:
                    ret = "couler.%s.%s.outputs.parameters.%s" % (
                        step_name,
                        template_name,
                        output_id,
                    )
                rets.append(OutputParameter(value=ret, is_global=is_global))
            else:
                if is_global:
                    ret = "couler.workflow.outputs.artifacts.%s" % output_id
                else:
                    ret = "couler.%s.%s.outputs.artifacts.%s" % (
                        step_name,
                        template_name,
                        output_id,
                    )
                rets.append(
                    OutputArtifact(
                        value=ret,
                        path=o["path"],
                        artifact=o,
                        is_global=is_global,
                    )
                )
    else:
        raise SyntaxError("Container output must be a list")

    return rets


def script_output(step_name, template_name):
    """Generate output name from an Argo script template.  For example,
    "{{steps.generate.outputs.result}}" in
    https://github.com/argoproj/argo/tree/master/examples#scripts--results
    Return of run_script is contacted by:
    couler.step_name.template_name.outputs.result
    """
    from couler.core.templates import OutputScript

    value = "couler.%s.%s.outputs.result" % (step_name, template_name)
    return [OutputScript(value=value)]


def job_output(step_name, template_name):
    """
    :param step_name:
    :param template_name:
    https://github.com/argoproj/argo/blob/master/examples/k8s-jobs.yaml#L44
    Return the job name and job id for running a job
    """
    job_name = "couler.%s.%s.outputs.parameters.job-name" % (
        step_name,
        template_name,
    )
    job_id = "couler.%s.%s.outputs.parameters.job-id" % (
        step_name,
        template_name,
    )
    job_obj = "couler.%s.%s.outputs.parameters.job-obj" % (
        step_name,
        template_name,
    )

    from couler.core.templates import OutputJob

    return [
        OutputJob(
            value=job_name, job_name=job_name, job_obj=job_obj, job_id=job_id
        )
    ]


def extract_step_return(step_output):
    """Extract information for run container or script output.
    step_output is a list with multiple outputs
    """
    from couler.core.templates import Output

    ret = {}
    if isinstance(step_output, list):
        # The first element of outputs is used for control flow operation
        step_output = step_output[0]
        # In case user input a normal variable
        if not isinstance(step_output, Output):
            ret["value"] = step_output
            return ret
        else:
            tmp = step_output.value.split(".")
            if len(tmp) < 4:
                raise ValueError("Incorrect step return representation")
            step_name = tmp[1]
            template_name = tmp[2]
            # To avoid duplicate map function
            output = tmp[3]
            for item in tmp[4:]:
                output = output + "." + item

            ret = {"name": template_name, "id": step_name, "output": output}
            return ret
    else:
        ret["value"] = step_output
        return ret


def invocation_name(function_name, caller_line):
    """Argo YAML requires that each step, which is an invocation to a
    template, has a name.  For example, hello1, hello2a, and hello2b
    in https://github.com/argoproj/argo/tree/master/examples#steps.
    However, in Python programs, there are no names for function
    invocations.  So we hype a name by the callee and where it is
    called.
    """
    return "%s-%s" % (function_name, caller_line)


def _parse_single_argo_output(output, prefix):
    from couler.core.templates import Output

    if isinstance(output, Output):
        tmp = output.value.split(".")
        if len(tmp) < 4:
            raise ValueError("Incorrect step return representation")
        step_name = tmp[1]
        output_id = tmp[3]
        for item in tmp[4:]:
            output_id = output_id + "." + item
        if output.is_global:
            return '"{{workflow.outputs.%s}}"' % output_id
        else:
            return '"{{%s.%s.%s}}"' % (prefix, step_name, output_id)
    else:
        # enforce int, float and bool types to string
        if (
            isinstance(output, int)
            or isinstance(output, float)
            or isinstance(output, bool)
        ):
            output = "'%s'" % output

        return output


def parse_argo_output(output, prefix):
    from couler.core.templates import Output, OutputJob

    if isinstance(output, OutputJob):
        return [
            _parse_single_argo_output(
                Output(value=output.job_id, is_global=output.is_global), prefix
            ),
            _parse_single_argo_output(
                Output(value=output.job_name, is_global=output.is_global),
                prefix,
            ),
            _parse_single_argo_output(
                Output(value=output.job_obj, is_global=output.is_global),
                prefix,
            ),
        ]
    else:
        return _parse_single_argo_output(output, prefix)


def load_cluster_config():
    """Load user provided cluster specification file.
    """
    module_file = os.getenv("couler_cluster_config")
    if module_file is None:
        return None
    from importlib import util

    spec = util.spec_from_file_location(module_file, module_file)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.cluster


def encode_base64(s):
    """
    Encode a string using base64 and return a binary string.
    This function is used in Secret creation.
    For example, the secrets for Argo YAML:
    https://github.com/argoproj/argo/blob/master/examples/README.md#secrets
    """
    bencode = base64.b64encode(s.encode("utf-8"))
    return str(bencode, "utf-8")


def generate_parameters_run_job(env):
    """
    Generate the inputs parameter for running kubernetes resource
    """
    from couler.core.templates import Output

    envs = []
    para_index = 0
    parameters = []
    args = []
    if env is not None:
        if isinstance(env, dict):
            for key in env:
                value = env[key]
                # in case the env value contains the other steps
                if key == "secrets":
                    if not isinstance(value, list):
                        raise ValueError(
                            "Secret environment should be a list."
                        )
                    envs.extend(value)
                elif key == "inferred_outputs":
                    for v in value:
                        v = parse_argo_output(v, prefix="tasks")
                        envs.append(
                            {
                                "name": "couler.inferred_outputs.%s"
                                % para_index,
                                "value": v,
                            }
                        )
                        para_index += 1
                elif (
                    isinstance(value, list)
                    and len(value) > 0
                    and isinstance(value[0], Output)
                ):
                    args.append(value[0].value)
                    para_name = input_parameter_name(
                        "run-job-para", para_index
                    )
                    parameters.append({"name": para_name})
                    env_value = "'{{input.parameters.%s}}'" % para_name
                    envs.append({"name": key, "value": env_value})
                    para_index = para_index + 1
                else:
                    envs.append({"name": key, "value": env[key]})
        else:
            raise TypeError("Input env need to be a dict")

    return envs, parameters, args


def convert_dict_to_env_list(d):
    """This is to convert a Python dictionary to a list, where
    each list item is a dict with `name` and `value` keys.
    """
    if not isinstance(d, dict):
        raise TypeError("The input parameter `d` is not a dict.")

    env_list = []
    for k, v in d.items():
        if isinstance(v, bool):
            value = "'%s'" % v
            env_list.append({"name": str(k), "value": value})
        elif k == "secrets":
            # TODO: only to add comments why "secrets" is special here
            if not isinstance(v, list):
                raise TypeError("The environment secrets should be a list.")
            for s in v:
                env_list.append(s)
        else:
            env_list.append({"name": str(k), "value": str(v)})
    return env_list


def config_retry_strategy(retry):
    """Generate retry strategy."""
    if not isinstance(retry, int):
        raise ValueError("Parameter retry should be a number")
    return {"limit": retry, "retryPolicy": "Always"}


def config_image_pull_policy(policy):
    if not isinstance(policy, ImagePullPolicy):
        raise AssertionError(
            "illegal imagePullPolicy, valid values: %s"
            % ImagePullPolicy.values()
        )
    return policy.value


def make_list_if_not(item):
    if item is None or isinstance(item, list):
        return item
    return [item]


def gpu_requested(resources):
    """
    Check whether the requested resources contains GPU.
    Here resources is a dict like {"cpu": 1, "memory": 2,...}.
    """
    if resources is None:
        return False
    if not isinstance(resources, dict):
        raise TypeError("Parameter resources is required to be a dict")
    for k, v in resources.items():
        if "gpu" in k.strip().lower() and int(v) > 0:
            return True
    return False


def non_empty(d):
    """
    Check whether the `collection` is none or empty.
    """
    return d is not None and len(d) > 0


def _get_uuid():
    import uuid

    """use uuid4 to gen ascii uuid, length=8"""
    return "".join(str(uuid.uuid4()).split("-"))[:8]
