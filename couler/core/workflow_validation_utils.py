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

import copy
import json

try:
    from argo.workflows import client
    from argo.workflows.client.models import (
        V1alpha1DAGTemplate,
        V1alpha1ResourceTemplate,
        V1alpha1ScriptTemplate,
        V1alpha1WorkflowStep,
    )

    _ARGO_INSTALLED = True
except ImportError:
    _ARGO_INSTALLED = False


def validate_workflow_yaml(original_wf):
    if _ARGO_INSTALLED:
        wf = copy.deepcopy(original_wf)
        if (
            "spec" not in wf
            or "templates" not in wf["spec"]
            or len(wf["spec"]["templates"]) <= 0
        ):
            if wf["kind"] == "CronWorkflow":
                if (
                    "workflowSpec" not in wf["spec"]
                    or "templates" not in wf["spec"]["workflowSpec"]
                    or len(wf["spec"]["workflowSpec"]["templates"]) <= 0
                ):
                    raise Exception(
                        "CronWorkflow yaml must contain "
                        "spec.workflowSpec.templates"
                    )
            else:
                raise Exception("Workflow yaml must contain spec.templates")
        if wf["kind"] == "CronWorkflow":
            templates = wf["spec"]["workflowSpec"]["templates"]
        else:
            templates = wf["spec"]["templates"]
        # Note that currently direct deserialization of `V1alpha1Template` is
        # problematic so here we validate them individually instead.
        for template in templates:
            if "steps" in template:
                if template["steps"] is None or len(template["steps"]) <= 0:
                    raise Exception(
                        "At least one step definition must exist in steps"
                    )
                for step in template["steps"]:
                    _deserialize_wrapper(step, V1alpha1WorkflowStep)
            elif "dag" in template:
                if (
                    template["dag"] is None
                    or "tasks" not in template["dag"]
                    or template["dag"]["tasks"] is None
                    or len(template["dag"]["tasks"]) <= 0
                ):
                    raise Exception(
                        "At least one task definition must exist in dag.tasks"
                    )
                _deserialize_wrapper(template["dag"], V1alpha1DAGTemplate)
            elif "resource" in template:
                _deserialize_wrapper(
                    template["resource"], V1alpha1ResourceTemplate
                )
            elif "script" in template:
                _deserialize_wrapper(
                    template["script"], V1alpha1ScriptTemplate
                )


def _deserialize_wrapper(dict_content, response_type):
    body = {"data": json.dumps(dict_content)}
    attr = type("Response", (), body)
    client.ApiClient().deserialize(attr, response_type)
