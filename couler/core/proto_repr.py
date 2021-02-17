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
    script_output=None,
    args=None,
    input=None,
    output=None,
    manifest=None,
    success_cond=None,
    failure_cond=None,
):
    assert step_name is not None
    assert tmpl_name is not None
    # generate protobuf step representation
    pb_step = couler_pb2.Step()
    pb_step.id = get_uniq_step_id()
    pb_step.name = step_name
    pb_step.tmpl_name = tmpl_name
    # image can be None if manifest specified.
    if image is not None:
        pb_step.container_spec.image = image
    if manifest is not None:
        pb_step.resource_spec.manifest = manifest
    if success_cond is not None:
        pb_step.resource_spec.success_condition = success_cond
        pb_step.resource_spec.failure_condition = failure_cond
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
                pb_art = couler_pb2.StepIO()
                pb_art.artifact.name = arg.artifact["name"]
                pb_art.artifact.value = (
                    '"{{inputs.artifacts.%s}}"' % pb_art.artifact.name
                )
                pb_step.args.append(pb_art)
            else:
                pb_param = couler_pb2.StepIO()
                pb_param.parameter.name = utils.input_parameter_name(
                    pb_step.name, i
                )
                pb_param.parameter.value = (
                    '"{{inputs.parameters.%s}}"' % pb_param.parameter.name
                )
                pb_step.args.append(pb_param)

    # add step to proto workflow
    concurrent_step = couler_pb2.ConcurrentSteps()
    concurrent_step.steps.append(pb_step)
    wf.steps.append(concurrent_step)
    return pb_step


def _add_io_to_template(
    pb_tmpl, source_step_id, input=None, output=None, script_output=None
):
    if script_output is not None:
        o = couler_pb2.StepIO()
        o.source = source_step_id
        o.stdout.name = script_output[0].value
        pb_tmpl.outputs.append(o)

    for i, io in enumerate([input, output]):
        if io is not None:
            # NOTE: run_job will pass type OutputJob here
            if isinstance(io, list) and isinstance(io[0], OutputJob):
                for oj in io:
                    o = couler_pb2.StepIO()
                    o.source = source_step_id
                    o.parameter.name = "job-name"
                    o.parameter.value = oj.job_name
                    pb_tmpl.outputs.append(o)

                    o = couler_pb2.StepIO()
                    o.source = source_step_id
                    o.parameter.name = "job-id"
                    o.parameter.value = oj.job_id
                    pb_tmpl.outputs.append(o)

                    o = couler_pb2.StepIO()
                    o.source = source_step_id
                    o.parameter.name = "job-obj"
                    o.parameter.value = oj.job_obj
                    pb_tmpl.outputs.append(o)
                break

            if "artifacts" in io:
                art_list = io["artifacts"]
                for art in art_list:
                    o = couler_pb2.StepIO()
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
                    if "key" in art:
                        a.remote_path = attrs["key"]
                    if "endpoint" in art:
                        a.endpoint = attrs["endpoint"]
                    if "bucket" in art:
                        a.bucket = attrs["bucket"]
                    if "accessKeySecret" in art:
                        a.access_key.name = attrs["accessKeySecret"]["name"]
                        a.access_key.key = attrs["accessKeySecret"]["key"]
                        s = states._secrets[a.access_key.name]
                        a.access_key.value = s.data[a.access_key.key]
                        a.secret_key.name = attrs["secretKeySecret"]["name"]
                        a.secret_key.key = attrs["secretKeySecret"]["key"]
                        s = states._secrets[a.secret_key.name]
                        a.secret_key.value = s.data[a.secret_key.key]
                    if "globalName" in art:
                        a.global_name = art["globalName"]
                    if i == 0:
                        pb_tmpl.inputs.append(o)
                    elif i == 1:
                        pb_tmpl.outputs.append(o)
            elif "parameters" in io:
                p_list = io["parameters"]
                for p in p_list:
                    o = couler_pb2.StepIO()
                    o.source = source_step_id
                    o.parameter.name = p["name"]
                    if "valueFrom" in p:
                        o.parameter.value = p["valueFrom"]["path"]
                    if i == 0:
                        pb_tmpl.inputs.append(o)
                    elif i == 1:
                        pb_tmpl.outputs.append(o)
