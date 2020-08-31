# Couler API Design

## What is Couler?

Many workflow engines exist nowadays, namely, [Apache Airflow](https://airflow.apache.org/),
[Kubeflow Pipelines](https://github.com/kubeflow/pipelines), and [Argo Workflows](https://github.com/argoproj/argo).
However, their programming experience varies and they have different level of abstractions
that are often obscure and complex. The code snippets below are some examples for constructing workflows
using Apache Airflow and Kubeflow Pipelines. 

<table>
<tr><th>Apache Airflow</th><th>Kubeflow Pipelines</th></tr>
<tr>
<td valign="top"><p>

```python
def create_dag(dag_id,
               schedule,
               dag_number,
               default_args):
    def hello_world_py(*args):
        print('Hello World')

    dag = DAG(dag_id,
              schedule_interval=schedule,
              default_args=default_args)
    with dag:
        t1 = PythonOperator(
            task_id='hello_world',
            python_callable=hello_world_py,
            dag_number=dag_number)
    return dag

for n in range(1, 10):
    default_args = {'owner': 'airflow',
                    'start_date': datetime(2018, 1, 1)
                    }
    globals()[dag_id] = create_dag(
        'hello_world_{}'.format(str(n)),
        '@daily',
        n,
        default_args)
```

</p></td>
<td valign="top"><p>

```python
class FlipCoinOp(dsl.ContainerOp):
    """Flip a coin and output heads or tails randomly."""
    def __init__(self):
        super(FlipCoinOp, self).__init__(
            name='Flip',
            image='python:alpine3.6',
            command=['sh', '-c'],
            arguments=['python -c "import random; result = \'heads\' if random.randint(0,1) == 0 '
                       'else \'tails\'; print(result)" | tee /tmp/output'],
            file_outputs={'output': '/tmp/output'})

class PrintOp(dsl.ContainerOp):
    """Print a message."""
    def __init__(self, msg):
        super(PrintOp, self).__init__(
            name='Print',
            image='alpine:3.6',
            command=['echo', msg],
        )

# define the recursive operation
@graph_component
def flip_component(flip_result):
    print_flip = PrintOp(flip_result)
    flipA = FlipCoinOp().after(print_flip)
    with dsl.Condition(flipA.output == 'heads'):
        flip_component(flipA.output)

@dsl.pipeline(
    name='pipeline flip coin',
    description='shows how to use graph_component.'
)
def recursive():
    flipA = FlipCoinOp()
    flipB = FlipCoinOp()
    flip_loop = flip_component(flipA.output)
    flip_loop.after(flipB)
    PrintOp('cool, it is over. %s' % flipA.output).after(flip_loop)
```

</p></td>
</tr>
</table>

Couler provides a unified interface for constructing and managing workflows that provides the following:

* Simplicity: unified interface and imperative programming style for defining workflows with automatic construction of directed acyclic graph (DAG).
* Extensibility: extensible to support various workflow engines.
* Reusability: Reusable templates for tasks such as distributed machine learning.
* Efficiency: Automatic workflow and resource optimizations under the hood.

An example workflow defined via Couler is shown below:

```python
def random_code():
    result = "heads" if random.randint(0, 1) == 0 else "tails"
    print(result)

def flip_coin():
    return couler.run_step(
        image="couler/python:3.6",
        source=random_code,
    )

def heads():
    return couler.run_step(
        image="couler/python:3.6",
        command=["bash", "-c", 'echo "it was heads"'],
    )

def tails():
    return couler.run_step(
        image="couler/python:3.6",
        command=["bash", "-c", 'echo "it was tails"'],
    )

result = flip_coin()
couler.when(couler.equal(result, "heads"), lambda: heads())
couler.when(couler.equal(result, "tails"), lambda: tails())
```

## Interfaces

Core operations (`couler.ops`):

* `run_step(step_def)` where `step_def` is the step definition that can be a container spec, Python function,
or spec that's specific to the underlying workflow engine (e.g. k8s CRD if Argo Workflow is used).

Control flow (`couler.control_flows`):

* `map(func, *args, **kwargs)` where `*args` and `**kwargs` correspond to various arguments passed to the function `func`.
* `when(cond, if_op, else_op)` where
    * `cond` can be any of the following predicates: `equal()`, `not_equal()`, `bigger()`, `smaller()`, `bigger_equal()`, `smaller_equal()`.
    * The operation defined in `if_op` will be executed when `cond` is true. Otherwise, `else_op` will be executed.
* `while_loop(cond, func, *args, **kwargs)` where
    * `cond` can be any one of the predicates mentioned above.
    *  `func`, `*args`, and `**kwargs` are similar to `map()`'s.

Utilities (`couler.utils`):

* `submit(config=workflow_config(schedule="* * * * 1"))`
* `get_status(workflow_name)`
* `get_logs(workflow_name)`
* `delete_workflow(workflow_name)`

Backends (`couler.backends`):

* `get_backend()`
* `use_backend("argo")`
