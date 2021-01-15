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

from io import StringIO

import yaml

import couler.argo as couler

katib_manifest_template = """
apiVersion: "kubeflow.org/v1alpha3"
kind: Experiment
metadata:
  labels:
    controller-tools.k8s.io: "1.0"
  generateName: katib-
spec:
  parallelTrialCount: {parallel_trial_count}
  maxTrialCount: {max_trial_count}
  maxFailedTrialCount: {max_failed_trial_count}
  objective:
    type: {obj_type}
    goal: {obj_goal}
    objectiveMetricName: {obj_metric_name}
  algorithm:
    algorithmName: {algorithm}
  trialTemplate:
    goTemplate:
      rawTemplate: |- {raw_template}
"""


def run(
    raw_template,
    tuning_params,
    objective,
    success_condition=None,
    failure_condition=None,
    algorithm="random",
    parallel_trial_count=3,
    max_trial_count=12,
    max_failed_trial_count=3,
):
    """
    Args:
        tuning_params: A dictionary of hyperparameters to be tuned.
        objective: The dictionary of objective for model training.
        success_condition: The condition to indicate when a Katib
            experiment succeeds.
        failure_condition: The condition to indicate when a Katib
            experiment fails.
        algorithm: The algorithm used in model training.
        raw_template: The YAML string for containing Katib trial manifest.
        parallel_trial_count: The number of parallel Katib trials.
        max_trial_count: The total number of Katib trials.
        max_failed_trial_count: The total number of failed Katib trials.
    """
    _validate_objective(objective)
    _validate_tuning_params(tuning_params)

    manifest = katib_manifest_template.format(
        parallel_trial_count=parallel_trial_count,
        max_trial_count=max_trial_count,
        max_failed_trial_count=max_failed_trial_count,
        obj_type=objective["type"],
        obj_goal=objective["goal"],
        obj_metric_name=objective["metric_name"],
        algorithm=algorithm,
        raw_template=raw_template,
    )

    wf_yaml = yaml.load(StringIO(manifest), Loader=yaml.FullLoader)

    parameters = []
    for i in range(0, len(tuning_params)):
        param = {
            "name": "--%s" % tuning_params[i]["name"],
            "parameterType": tuning_params[i]["type"],
            "feasibleSpace": {
                "min": '"%d"' % tuning_params[i]["range"][0],
                "max": '"%d"' % tuning_params[i]["range"][1],
            },
        }
        parameters.append(param)

    wf_yaml["spec"]["parameters"] = parameters

    manifest = yaml.dump(wf_yaml, default_flow_style=False)
    couler.run_job(
        manifest=manifest,
        success_condition=success_condition,
        failure_condition=failure_condition,
    )


def _validate_objective(objective):
    if (
        "type" not in objective
        or "goal" not in objective
        or "metric_name" not in objective
    ):
        raise ValueError(
            "Parameter objective should include type, goal and metric_name."
        )


def _validate_tuning_params(tuning_params):
    if not isinstance(tuning_params, list):
        raise TypeError("Parameter tuning_params should be a list.")

    for param in tuning_params:
        if not isinstance(param, dict):
            raise TypeError("Each tuning parameter should be a dict.")

        if (
            "name" not in param
            or "type" not in param
            or "range" not in param
            or not isinstance(param["range"], list)
            or len(param["range"]) != 2
        ):
            raise ValueError(
                "Each tuning parameter should include name, type and range."
            )
