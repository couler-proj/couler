# Couler Tekton Design

This document outlines the design of tekton backend for core Couler APIs.

## Goals

* Design the tekton backend implementation for core Couler APIs.

## Non-Goals

* Provide implementation details.

## Design

Based on the core [Couler APIs design](couler-api-design.md), we can see the definitions in different workflow engines.

| Couler | Argo | Tekton |
| ---- | ---- | ---- |
| Step | Step | Step |
| Reusable step | Template | Task |
| Workflow | Workflow | Pipeline |

* `Step` is the smallest unit and remain consistent across different backends so the core operation `run_step(step_def)` will also keep consistent. In tekton, the definition of `step` and `container` keeps the same, which means that if users pass a python function to step, the backend should wrap the function in a python base image automatically.

### Control Flow

#### `when(cond, if_op, else_op)`

In the latest v0.16 version of Tekton, the condition field is deprecated and Tekton uses [whenExpression](https://github.com/tektoncd/pipeline/blob/master/docs/pipelines.md#guard-task-execution-using-whenexpressions) instead. Here is an example:

```yaml
tasks:
  - name: echo-file-exists
    when:
      - input: "$(tasks.check-file.results.exists)"
        operator: in
        values: ["yes"]
    taskRef:
        name: echo-file-exists
```

A `whenExpression` is made of `Input`, `Operator` and `Values`. The `Input` can be static inputs or variables (Parameters or Results in Tekton). The `Operator` can be either `in` or `notin`.
As we can see, there is no `else_op` in Tekton, so we need to convert the `else` in the Tekton backend, which is pretty simple since there is only `in` and `notin` operator, we can simply change the operator in the "else" task like:
```yaml
tasks:
  - name: echo-file-not-exists
    when:
      - input: "$(tasks.check-file.results.exists)"
        operator: notin
        values: ["yes"]
    taskRef:
        name: echo-file-not-exists
```


#### `while_loop(cond, func, *args, **kwargs)`

There is no native support for loops in Tekton for now. See this [issue](https://github.com/tektoncd/pipeline/issues/2050) for more information.

### Couler Utilities:

The `get_status`, `get_logs` remains the same as the Argo design.

* `submit(config=workflow_config(schedule="* * * * 1"))`: There is no native support for cron in Tekton, see this [issue](https://github.com/tektoncd/triggers/issues/69) for more information. The community recommend cronjob in kubernetes, see [example](https://github.com/tektoncd/triggers/blob/master/examples/cron/README.md) here. For couler, we can wrap the `cron` in the workflow and let backend to handle the work like create `CronJob` in Kubernetes.
* `delete_workflow(workflow_name)`: To be discussed: should we delete the tasks when delete the pipeline?
* `list_workflow_records(workflow_name)`: After submitting the workflow(create PipelineRun in Tekton), there will be numbers of workflow records. A list function is necessary for users to show all the records.

### Other Tekton Utilities

* [Finally](https://github.com/tektoncd/pipeline/blob/master/docs/pipelines.md#adding-finally-to-the-pipeline): Finally is a unique feature of Tekton. With finally, the Final tasks are guaranteed to be executed in parallel after all PipelineTasks under tasks have completed regardless of success or error. For example:
```yaml
spec:
  tasks:
    - name: tests
      taskRef:
        Name: integration-test
  finally:
    - name: cleanup-test
      taskRef:
        Name: cleanup
```

In Couler, we can have `run_finally(finally_def)` function which is only available when the backend is Tekton.