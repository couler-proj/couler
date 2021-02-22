# Copyright 2021 The Couler Authors. All rights reserved.
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


class Output(object):
    def __init__(self, value, is_global=False):
        self.value = value
        self.is_global = is_global


class OutputEmpty(Output):
    def __init__(self, value, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)


class OutputParameter(Output):
    def __init__(self, value, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)


class OutputArtifact(Output):
    def __init__(self, value, path, artifact, is_global=False, type=""):
        Output.__init__(self, value=value, is_global=is_global)
        self.path = path
        self.artifact = artifact
        self.type = type


class OutputScript(Output):
    def __init__(self, value, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)


class OutputJob(Output):
    def __init__(self, value, job_name, job_id, job_obj=None, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)
        self.job_name = job_name
        self.job_id = job_id
        self.job_obj = job_obj


def _parse_single_argo_output(output, prefix):

    if isinstance(output, Output):
        tmp = output.value.split(".")
        if "artifacts" in tmp:
            return output
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


def _container_output(step_name, template_name, output):
    """Generate output name from an Argo container template.  For example,
    "{{steps.generate-parameter.outputs.parameters.hello-param}}" used in
    https://github.com/argoproj/argo/tree/master/examples#output-parameters.
    Each element of return for run_container is contacted by:
    couler.step_name.template_name.output.parameters.output_id
    """

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


def _script_output(step_name, template_name, output):
    """Generate output name from an Argo script template.  For example,
    "{{steps.generate.outputs.result}}" in
    https://github.com/argoproj/argo/tree/master/examples#scripts--results
    Return of run_script is contacted by:
    couler.step_name.template_name.outputs.result
    """
    value = "couler.%s.%s.outputs.result" % (step_name, template_name)
    output_script = OutputScript(value=value)

    if output is None:
        return [output_script]

    rets = _container_output(step_name, template_name, output)
    rets.append(output_script)

    return rets


def _job_output(step_name, template_name):
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

    return [
        OutputJob(
            value=job_name, job_name=job_name, job_obj=job_obj, job_id=job_id
        )
    ]


def extract_step_return(step_output):
    """Extract information for run container or script output.
    step_output is a list with multiple outputs
    """

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
