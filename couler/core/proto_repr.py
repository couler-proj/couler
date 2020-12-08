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

from couler.core import utils
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
    input=None,
    output=None,
):
    assert step_name is not None
    assert tmpl_name is not None
    assert image is not None
    # generate protobuf step representation
    pb_step = couler_pb2.Step()
    pb_step.id = get_uniq_step_id()
    pb_step.name = step_name
    pb_step.tmpl_name = tmpl_name
    pb_step.image = image
    if command is None:
        pb_step.command.append("python")
    elif isinstance(command, list):
        pb_step.command.extend(command)
    elif isinstance(command, str):
        pb_step.command.append(command)
    else:
        raise ValueError("command must be str or list")
    if source is not None:
        if isinstance(source, str):
            pb_step.script = source
        else:
            pb_step.script = utils.body(source)

    if script_output is not None:
        o = couler_pb2.StepIO()
        o.source = pb_step.id
        o.stdout.name = script_output[0].value
        pb_step.outputs.append(o)

    for i, io in enumerate([input, output]):
        if io is not None:
            if "artifacts" in io:
                art_list = io["artifacts"]
                for a in art_list:
                    o = couler_pb2.StepIO()
                    o.source = pb_step.id
                    o.artifact.name = a["name"]
                    if "oss" in a:
                        o.artifact.type = "OSS"
                    elif "s3" in a:
                        o.artifact.type = "S3"
                    o.artifact.value = a["path"]
                    # TODO(typhoonzero): add artifact details from:
                    # templates/artifact.py
                    if i == 0:
                        pb_step.inputs.append(o)
                    elif i == 1:
                        pb_step.outputs.append(o)
            elif "parameters" in io:
                p_list = io["parameters"]
                for p in p_list:
                    o = couler_pb2.StepIO()
                    o.source = pb_step.id
                    o.parameter.name = p["name"]
                    if "valueFrom" in p:
                        o.parameter.value = p["valueFrom"]["path"]
                    if i == 0:
                        pb_step.inputs.append(o)
                    elif i == 1:
                        pb_step.outputs.append(o)
    # add step to proto workflow
    wf = get_default_proto_workflow()
    wf.steps.append(pb_step)
    return pb_step
