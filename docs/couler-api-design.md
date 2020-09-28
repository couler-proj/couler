# Couler API Design

This document outlines the design of core Couler APIs to support multiple workflow backends. Please see
[this RFC](https://github.com/couler-proj/couler/pull/24) for the initial design discussions.

## Goals

* Design the core Couler APIs that can be implemented across different workflow engines.
* Provide a *minimal* set of APIs that are forward-looking, engine-agnostic, and less likely to deprecate over-time.

## Non-Goals

* Provide an exhaustive set of APIs that cover all use cases and all workflow engines.
* Provide implementation details.

## Design

Core operations (`couler.ops`):

* `run_step(step_def)` where `step_def` is the step definition that can be a container spec, Python function,
or spec that's specific to the underlying workflow engine (e.g. k8s CRD if Argo Workflow is used). A "step"
represents a node in the workflow graph, e.g. the "smallest" unit in some sense. For an analogy
of a Couler "step" in different backends, please see the last section for a table of various Couler concepts.

Control flow (`couler.control_flows`):

* `map(func, *args, **kwargs)` where `*args` and `**kwargs` correspond to various arguments passed to the function `func`.
* `when(cond, if_op, else_op)` where
    * `cond` can be any of the following predicates: `equal()`, `not_equal()`, `bigger()`, `smaller()`, `bigger_equal()`, `smaller_equal()`.
    * The operation defined in `if_op` will be executed when `cond` is true. Otherwise, `else_op` will be executed.
* `while_loop(cond, func, *args, **kwargs)` where
    * `cond` can be any one of the predicates mentioned above.
    *  `func`, `*args`, and `**kwargs` are similar to `map()`'s.

Utilities (`couler.utils`):

* `submit(config=workflow_config(schedule="* * * * 1"))` where `config` is engine-specific.
* `get_status(workflow_name)`
* `get_logs(workflow_name)`
* `delete_workflow(workflow_name)`

Backends (`couler.backends`):

* `get_backend()`
* `use_backend("argo")`

## Minimal Working Workflow Example

An example workflow defined via some of the APIs mentioned above is shown below:

```python
import couler
import random

if couler.get_backend() != "argo":
    couler.use_backend("argo")

def random_code():
    result = "heads" if random.randint(0, 1) == 0 else "tails"
    print(result)

def flip_coin():
    return couler.run_step(
        image="python:alpine3.6",
        step_def=random_code,
    )

def heads():
    return couler.run_step(
        image="alpine:3.6",
        step_def=["bash", "-c", 'echo "it was heads"'],
    )

def tails():
    return couler.run_step(
        image="alpine:3.6",
        step_def=["bash", "-c", 'echo "it was tails"'],
    )

result = flip_coin()
couler.when(couler.equal(result, "heads"), lambda: heads())
couler.when(couler.equal(result, "tails"), lambda: tails())

name = couler.submit(config=workflow_config(schedule="* * * * 1"))

while couler.get_status(name) == "Running":
    if couler.get_status(name) == "Completed":
        couler.delete_workflow(name)
        break
```

## Concepts Analogies in Different Backends

To help visualize various concepts and their analogies in different Backends,
below is an attempt to compare them in a table which will be updated over time as
support for new backends is proposed:

| Concept\Framework| Couler        | Argo     | Tekton   | Airflow                                                             | Dagster         | Prefect |
| ---------------- | -------------- | -------- | -------- | ------------------------------------------------------------------- | --------------- | ------- |
| Step             | Step           | Step     | Step     | Task                                                                | Solid           | Task    |
| Composite step   | Reusable step  | Template | Task     | SubDag or TaskGroup                                                 | Composite Solid | TBA     |
| Worfklow         | Workflow       | Workflow | Pipeline | DAG                                                                 | Pipeline        | Flow    |

Note that by "reusable step", we mean parameterized templates that can be used to define a Couler step where users only have to specify a few parameters.

[Concepts Analogies in Different Backends]: #concepts-analogies
