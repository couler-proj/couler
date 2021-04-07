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

import json

from couler.core import states, utils  # noqa: F401
from couler.core.templates.output import OutputArtifact, OutputJob
from couler.proto import couler_pb2

DEFAULT_WORKFLOW = None
STEP_ID = 0


def get_default_proto_workflow():
    global DEFAULT_WORKFLOW
    if DEFAULT_WORKFLOW is None:
        DEFAULT_WORKFLOW = couler_pb2.Workflow()
        DEFAULT_WORKFLOW.parallelism = -1
    return DEFAULT_WORKFLOW


def cleanup_proto_workflow():
    global DEFAULT_WORKFLOW
    global STEP_ID
    DEFAULT_WORKFLOW = None
    STEP_ID = 0


def get_uniq_step_id():
    global STEP_ID
    STEP_ID += 1
    return STEP_ID


def step_repr(
    step_name=None,
    tmpl_name=None,
    image=None,
    command=None,
    source=None,
    env=None,
    script_output=None,
    args=None,
    input=None,
    output=None,
    manifest=None,
    success_cond=None,
    failure_cond=None,
    canned_step_name=None,
    canned_step_args=None,
    resources=None,
    secret=None,
    action=None,
    volume_mounts=None,
    cache=None,
):
    assert step_name is not None
    assert tmpl_name is not None
    # generate protobuf step representation
    pb_step = couler_pb2.Step()
    pb_step.id = get_uniq_step_id()
    pb_step.name = step_name
    pb_step.tmpl_name = tmpl_name

    if env is not None:
        _add_env_to_step(pb_step, env)

    if secret is not None:
        for k, _ in secret.data.items():
            pb_secret = pb_step.secrets.add()
            pb_secret.key = k
            pb_secret.name = secret.name

    if cache is not None:
        pb_step.cache.name = cache.name
        pb_step.cache.key = cache.key
        pb_step.cache.max_age = cache.max_age

    # image can be None if manifest specified.
    if image is not None:
        pb_step.container_spec.image = image
    if manifest is not None:
        pb_step.resource_spec.manifest = manifest
        if success_cond is not None and failure_cond is not None:
            pb_step.resource_spec.success_condition = success_cond
            pb_step.resource_spec.failure_condition = failure_cond
        if action is not None:
            pb_step.resource_spec.action = action
    else:
        if command is None:
            pb_step.container_spec.command.append("python")
        elif isinstance(command, list):
            pb_step.container_spec.command.extend(command)
        elif isinstance(command, str):
            pb_step.container_spec.command.append(command)
        else:
            raise ValueError("command must be str or list")
    if source is not None:
        if isinstance(source, str):
            pb_step.script = source
        else:
            pb_step.script = utils.body(source)
    if canned_step_name is not None and canned_step_args is not None:
        pb_step.canned_step_spec.name = canned_step_name
        if isinstance(canned_step_args, dict):
            for k, v in canned_step_args.items():
                pb_step.canned_step_spec.args[k] = v
        else:
            raise ValueError("canned_step_spec.args must be a dictionary")

    # setup resources
    if resources is not None:
        if not isinstance(resources, dict):
            raise ValueError("resources must be type dict")
        for k, v in resources.items():
            # key: cpu, memory, gpu
            # value: "1", "8", "500m", "1Gi" etc.
            pb_step.container_spec.resources[k] = str(v)

    # Attach volume mounts
    if volume_mounts is not None:
        for vm in volume_mounts:
            vol_mount = pb_step.container_spec.volume_mounts.add()
            vol_mount.name = vm.name
            vol_mount.path = vm.mount_path

    if states._when_prefix is not None:
        pb_step.when = states._when_prefix

    # add template to proto workflow
    wf = get_default_proto_workflow()
    if tmpl_name not in wf.templates:
        proto_step_tmpl = couler_pb2.StepTemplate()
        proto_step_tmpl.name = tmpl_name
        _add_io_to_template(
            proto_step_tmpl, pb_step.id, input, output, script_output
        )
        wf.templates[tmpl_name].CopyFrom(proto_step_tmpl)

    # add step arguments
    if args is not None:
        for i, arg in enumerate(args):
            if isinstance(arg, OutputArtifact):
                pb_art = pb_step.args.add()
                pb_art.artifact.name = arg.artifact["name"]
                pb_art.artifact.value = arg.value
            else:
                pb_param = pb_step.args.add()
                pb_param.parameter.name = utils.input_parameter_name(
                    pb_step.name, i
                )
                pb_param.parameter.value = (
                    # This is casted to string for protobuf and Argo
                    # will automatically convert it to a correct type.
                    str(arg)
                    if isinstance(arg, (str, float, bool, int))
                    else arg.value
                )

    if states._exit_handler_enable:
        # add exit handler steps
        eh_step = wf.exit_handler_steps.add()
        eh_step.CopyFrom(pb_step)
    else:
        # add step to proto workflow
        concurrent_step = wf.steps.add()
        inner_step = concurrent_step.steps.add()
        inner_step.CopyFrom(pb_step)
    return pb_step


# append env to step spec
def _add_env_to_step(pb_step, env):
    for k, v in env.items():
        if isinstance(v, str):
            pb_step.container_spec.env[k] = v
        else:
            pb_step.container_spec.env[k] = json.dumps(v)


def add_deps_to_step(step_name):
    dag_task = states.workflow.get_dag_task(step_name)
    deps = dag_task.get("dependencies") if dag_task is not None else None
    if deps is not None:
        proto_wf = get_default_proto_workflow()
        step_id = None
        for i, step in enumerate(proto_wf.steps):
            if step.steps[0].name == step_name:
                step_id = i
                break
        if step_id is not None:
            proto_wf.steps[step_id].steps[0].dependencies.extend(deps)


def _add_io_to_template(
    pb_tmpl, source_step_id, input=None, output=None, script_output=None
):
    if script_output is not None:
        o = pb_tmpl.outputs.add()
        o.source = source_step_id
        o.stdout.name = script_output[0].value

    for i, io in enumerate([input, output]):
        if io is not None:
            # NOTE: run_job will pass type OutputJob here
            if isinstance(io, list) and isinstance(io[0], OutputJob):
                for oj in io:
                    o = pb_tmpl.outputs.add()
                    o.source = source_step_id
                    o.parameter.name = "job-name"
                    o.parameter.value = oj.job_name

                    o = pb_tmpl.outputs.add()
                    o.source = source_step_id
                    o.parameter.name = "job-id"
                    o.parameter.value = oj.job_id

                    o = pb_tmpl.outputs.add()
                    o.source = source_step_id
                    o.parameter.name = "job-obj"
                    o.parameter.value = oj.job_obj
                break

            if "artifacts" in io:
                art_list = io["artifacts"]
                for art in art_list:
                    if i == 0:
                        o = pb_tmpl.inputs.add()
                    elif i == 1:
                        o = pb_tmpl.outputs.add()
                    o.source = source_step_id
                    o.artifact.name = art["name"]
                    o.artifact.local_path = art["path"]
                    attrs = None
                    if "oss" in art:
                        o.artifact.type = "OSS"
                        attrs = art["oss"]
                    elif "s3" in art:
                        o.artifact.type = "S3"
                        attrs = art["s3"]
                    # NOTE: attrs["key"] stores the remote path on OSS/S3.
                    a = o.artifact
                    if attrs:
                        if "key" in attrs:
                            a.remote_path = attrs["key"]
                        if "endpoint" in attrs:
                            a.endpoint = attrs["endpoint"]
                        if "bucket" in attrs:
                            a.bucket = attrs["bucket"]
                        if "accessKeySecret" in attrs:
                            a.access_key.name = attrs["accessKeySecret"][
                                "name"
                            ]
                            a.access_key.key = attrs["accessKeySecret"]["key"]
                            s = states._secrets[a.access_key.name]
                            a.access_key.value = s.data[a.access_key.key]
                            a.secret_key.name = attrs["secretKeySecret"][
                                "name"
                            ]
                            a.secret_key.key = attrs["secretKeySecret"]["key"]
                            s = states._secrets[a.secret_key.name]
                            a.secret_key.value = s.data[a.secret_key.key]
                        if "globalName" in art:
                            a.global_name = art["globalName"]
            elif "parameters" in io:
                p_list = io["parameters"]
                for p in p_list:
                    if i == 0:
                        o = pb_tmpl.inputs.add()
                    elif i == 1:
                        o = pb_tmpl.outputs.add()
                    o.source = source_step_id
                    o.parameter.name = p["name"]
                    if "valueFrom" in p:
                        o.parameter.value = p["valueFrom"]["path"]
