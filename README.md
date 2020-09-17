[![CI](https://github.com/couler-proj/couler/workflows/CI/badge.svg)](https://github.com/couler-proj/couler/actions?query=event%3Apush+branch%3Amaster)
[![Slack](https://img.shields.io/badge/Slack-Couler-brightgreen.svg?logo=slack)](https://join.slack.com/t/couler/shared_invite/zt-h4hew4jm-LCZK1qr03bsMS5zZbCEc_g)
[![Twitter](https://img.shields.io/badge/@CoulerProject--_.svg?style=social&logo=twitter)](https://twitter.com/CoulerProject)

# Couler

## What is Couler?

Couler aims to provide a unified interface for constructing and managing workflows on
different workflow engines, such as [Argo Workflows](https://github.com/argoproj/argo), [Tekton Pipelines](https://tekton.dev/), and [Apache Airflow](https://airflow.apache.org/).

## Why use Couler?

Many workflow engines exist nowadays, e.g. [Argo Workflows](https://github.com/argoproj/argo), [Tekton Pipelines](https://tekton.dev/), and [Apache Airflow](https://airflow.apache.org/).
However, their programming experience varies and they have different level of abstractions
that are often obscure and complex. The code snippets below are some examples for constructing workflows
using Apache Airflow and [Kubeflow Pipelines](https://github.com/kubeflow/pipelines/).

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

### Coin Flip

This example combines the use of a Python function result, along with conditionals,
to take a dynamic path in the workflow. In this example, depending on the result
of the first step defined in `flip_coin()`, the template will either run the
`heads()` step or the `tails()` step.

Steps can be defined via either `couler.run_script()`
for Python functions or `couler.run_container()` for containers. In addition,
the conditional logic to decide whether to flip the coin in this example
is defined via the combined use of `couler.when()` and `couler.equal()`.

```python
import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter


def random_code():
    import random

    res = "heads" if random.randint(0, 1) == 0 else "tails"
    print(res)


def flip_coin():
    return couler.run_script(image="python:alpine3.6", source=random_code)


def heads():
    return couler.run_container(
        image="alpine:3.6", command=["sh", "-c", 'echo "it was heads"']
    )


def tails():
    return couler.run_container(
        image="alpine:3.6", command=["sh", "-c", 'echo "it was tails"']
    )


result = flip_coin()
couler.when(couler.equal(result, "heads"), lambda: heads())
couler.when(couler.equal(result, "tails"), lambda: tails())

submitter = ArgoSubmitter()
couler.run(submitter=submitter)
```

### DAG

This example demonstrates different ways to define the workflow as a directed-acyclic graph (DAG) by specifying the
dependencies of each task via `couler.set_dependencies()` and `couler.dag()`. Please see the code comments for the
specific shape of DAG that we've defined in `linear()` and `diamond()`.

```python
import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter


def job_a(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="A",
    )


def job_b(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="B",
    )


def job_c(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="C",
    )


def job_d(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="D",
    )

#     A
#    / \
#   B   C
#  /
# D
def linear():
    couler.set_dependencies(lambda: job_a(message="A"), dependencies=None)
    couler.set_dependencies(lambda: job_b(message="B"), dependencies=["A"])
    couler.set_dependencies(lambda: job_c(message="C"), dependencies=["A"])
    couler.set_dependencies(lambda: job_d(message="D"), dependencies=["B"])


#   A
#  / \
# B   C
#  \ /
#   D
def diamond():
    couler.dag(
        [
            [lambda: job_a(message="A")],
            [lambda: job_a(message="A"), lambda: job_b(message="B")],  # A -> B
            [lambda: job_a(message="A"), lambda: job_c(message="C")],  # A -> C
            [lambda: job_b(message="B"), lambda: job_d(message="D")],  # B -> D
            [lambda: job_b(message="C"), lambda: job_d(message="D")],  # C -> D
        ]
    )


linear()
submitter = ArgoSubmitter()
couler.run(submitter=submitter)
```

Note that the current version only works with Argo Workflows but we are actively working on the design of the unified
interface that is extensible to additional workflow engines. Please stay tuned for more updates and we welcome
any feedback and contributions from the community.

## Community Blogs and Presentations

* [Argo Workflows & Events Community Meeting, September 2020](https://docs.google.com/presentation/d/11KVEkKQGeV3R_-nHdqlzQV2uOrya94ra6Ilm_k6RwE4/edit?usp=sharing)
