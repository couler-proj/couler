# Couler Step Zoo

This document introduces the Couler Step Zoo, which consists of a collection of pre-defined and reusable steps that can
be used directly as part of a workflow defined using Couler.


## Existing Steps

Currently, Couler Step Zoo consists of the following pre-defined steps:

| Name | Description | API |
| ---- | ----------- | --- |
| MPI | Submit MPI-based distributed jobs via Kubeflow MPI Operator | `couler.steps.mpi.train()` |
| TensorFlow  | Submit TensorFlow distributed training jobs via Kubeflow TF Operator | `couler.steps.tensorflow.train()` |
| PyTorch  | Submit PyTorch distributed training jobs via Kubeflow PyTorch Operator | `couler.steps.pytorch.train()` |
| Katib  | Submit AutoML experiments (e.g. hyperparameter tuning and neural architecture search) via Kubeflow Katib | `couler.steps.katib.run()` |

If you'd like to add a new pre-defined steps to the Couler Step Zoo, please see the following sections for
the specific requirements and instructions.


## Requirements on New Steps

In order to provide a consistent and friendly experience to our users, below are the requirements for a new pre-defined
step to be eligible for inclusion in Couler Step Zoo:

* It should be completely implemented using the core [Couler APIs](couler-api-design.md).
* It should expose backend specific configurations instead of hard-coding them.
* It should have a clear set of dependencies that can be easily installed with sufficient instructions.
* When possible, proving a minimal set of unit tests and integration tests to make sure the step functions correctly.


## Adding a Pre-defined Step

To add a pre-defined step to the Couler Step Zoo, please follow the instructions below.

1. Make sure the step meets the list of requirements in the above section.
1. Add the step implementation to [couler.steps module](../couler/steps). The interface would look like the following:

```python
def random_code():
    import random

    res = "heads" if random.randint(0, 1) == 0 else "tails"
    print(res)

def run_heads(
    image="alpine:3.6",
    command=["sh", "-c", 'echo "it was heads"'],
):
    result = random_code()
    couler.when(
        couler.equal(result, "heads"),
        lambda: couler.run_step(
            command=command,
            image=image,
    ))
```

Here we implemented a pre-defined step `run_heads()` that could run a specified command such as `["sh", "-c", 'echo "it was heads"']`
if `random_code()` returns `"heads"`. Note that the step should be completely implemented using the
core [Couler APIs](couler-api-design.md) in order to work well with different Couler backends.

You can find reference step implementations [here](../couler/steps).

1. Provide minimal set of [unit test](../couler/tests) and [integration test](../integration_tests) when possible.
1. Provide necessary user-facing documentation in the API docstring, including documentation on each arguments in the
step signature and the system dependencies.


## Alternatives Considered

Some workflow engines or frameworks provide their own library for distributing the set of reusable steps/tasks/components, for example:

* [Argo Workflows catalog](https://github.com/argoproj-labs/argo-workflows-catalog)
* [Prefect tasks library](https://docs.prefect.io/core/task_library/overview.html#task-library-in-action)
* [KFP components](https://github.com/kubeflow/pipelines/tree/master/components)
* [Tekton tasks/pipelines catalog](https://github.com/tektoncd/catalog)

Even though it's relatively easier to provide wrappers around the existing reusable libraries, there are some issues
with that approach:

* It's hard to maintain and keep the wrappers up-to-date.
* It's non-trivial to provide a consistent interface that would work across different backends.
* This would introduce bad user experience due to feature parity across those reusable libraries implemented for different backends.
