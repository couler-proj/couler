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
    tuning_params=None,
    objective=None,
    success_condition=None,
    failure_condition=None,
    raw_template=None,
    algorithm="random",
    parallel_trial_count=3,
    max_trial_count=12,
    max_failed_trial_count=3,
):
    # Args:
    #   tuning_params: [
    #       {"name": "max_depth" , "type": "int", "range": [2, 10]},
    #       ...,
    #   ], to specify the hyperparameters will be tuned.
    #   objective: {"type": "..." , "goal": "...", "metric_name": "..."},
    #     to specify the objective of the model training,
    #   success_condition: str, the condition which indicates
    #     katib experiment succeeds,
    #   failure_condition: str, the condition which indicates
    #     katib experiment fails,
    #   algorithm: str, the algorithm used in model training,
    #   raw_template: str, the YAML string for particular training job,
    #   parallel_trial_count: int, the number of katib training jobs
    #     which execute in parallel,
    #   max_trial_count: int, the total number of katib training jobs,
    #   max_failed_trial_count: int, the number of failed katib training jobs,
    #     which indicates katib experiment fails.

    # Check required parameters
    _validate_raw_template(raw_template)
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


def _validate_raw_template(raw_template):
    if raw_template is None:
        raise ValueError("Parameter raw_template should not be null.")


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
            raise TypeError("Each tunning parameter should be a dict.")

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
