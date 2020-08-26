[![CI](https://github.com/couler-proj/couler/workflows/CI/badge.svg)](https://github.com/couler-proj/couler/actions?query=event%3Apush+branch%3Amaster)

# Couler

## What is Couler?

Couler is a project that aims to provide a unified interface for constructing and managing workflows on
different workflow engines, such as [Argo Workflows](https://github.com/argoproj/argo) and [Apache Airflow](https://airflow.apache.org/).

## Why use Couler?

Many workflow engines exist nowadays, e.g. [Apache Airflow](https://airflow.apache.org/), [Kubeflow Pipelines](https://github.com/kubeflow/pipelines), and [Argo Workflows](https://github.com/argoproj/argo).
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

* Simplicity: Unified interface and imperative programming style for defining workflows with automatic construction of directed acyclic graph (DAG).
* Extensibility: Extensible to support various workflow engines.
* Reusability: Reusable steps for tasks such as distributed training of machine learning models.
* Efficiency: Automatic workflow and resource optimizations under the hood.

Please see the following sections for installation guide and examples.

## Installation

* Couler currently only supports Argo Workflows. Please see instructions [here](https://argoproj.github.io/argo/quick-start/#install-argo-workflows)
to install Argo Workflows on your Kubernetes cluster.
* Install Python 3.6+
* Install Couler Python SDK via the following `pip` command:

```bash
pip install git+https://github.com/couler-proj/couler
```
Alternatively, you can clone this repository and then run the following to install:

```bash
python setup.py install
```

## Examples

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

