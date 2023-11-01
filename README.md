# Couler

## What is Couler?

* Couler is a system designed for unified machine learning workflow optimization in the cloud. Couler endeavors to provide a unified interface for constructing and optimizing workflows across various workflow engines, such as [Argo Workflows](https://github.com/argoproj/argo-workflows), [Tekton Pipelines](https://tekton.dev/), and [Apache Airflow](https://airflow.apache.org/). Couler enhances workflow efficiency through features like Autonomous Workflow Construction, Automatic Artifact Caching Mechanisms, Big Workflow Auto Parallelism Optimization, and Automatic Hyperparameters Tuning.
* Couler is included in [CNCF Cloud Native Landscape](https://landscape.cncf.io/) and [LF AI Landscape](https://landscape.lfai.foundation).
* The technical report for Couler can be found at the following link: [Techinal-Report](https://github.com/couler-proj/couler/tree/master/docs/Technical-Report-of-Couler)

> Note that while one of ambitious goals of Couler is to support multiple workflow engines, Couler currently only supports Argo Workflows as the workflow orchestration backend. An ambitious goal of Couler is to provide support for multiple workflow engines. While it initially supported only Argo Workflows for workflow orchestration, efforts are now underway to extend support to other workflow engines such as Tekton Pipelines and Apache Airflow.
> In addition, if you are looking for a Python SDK that provides access to all the available features from Argo Workflows, you might want to check out [the low-level Python SDK maintained by the Argo Workflows team](https://argoproj.github.io/argo-workflows/client-libraries/).


## Who uses Couler?

You can find a list of organizations who are using Couler in [ADOPTERS.md](ADOPTERS.md). If you'd like to add your organization to the list, please send us a pull request.

## Why use Couler?

Many workflow engines exist nowadays, e.g. [Argo Workflows](https://github.com/argoproj/argo-workflows), [Tekton Pipelines](https://tekton.dev/), and [Apache Airflow](https://airflow.apache.org/).
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

Couler is a system for unified Mechine Learning (ML) workflow optimization in cloud and the contributions are outlined below::

* Simplicity and Extensibility: Couler provides a unified programming interface for workflow definition, ensuring independence from the workflow engine and compatibility with various workflow engines such as Argo Workflows, Airflow, and Tekton. 
* Automation: Couler integrates LLMs in unified programming code generation. By leveraging LLMs, Couler facilitates the generation of unified programming code using NL descriptions. Additionally, we automate hyperparameters tuning through the integration of Dataset Card and Model Card, enhancing the effectiveness of the autoML process.
* Efficiency: Couler introduces the Intermediate Representative (IR) to depict the workflow Directed Acyclic Graph (DAG), optimizing extensive workflow computations by dividing a large workflow into smaller ones for auto-parallelism optimization. Couler also implements dynamic caching of artifacts, which are the outputs of jobs in the workflow, to minimize redundant computations and ensure fault tolerance.
* Open Source Community: The released open-source version of Couler has garnered adoption from multiple companies and end-users. For instance, over 3000 end users are utilizing Couler within Ant Group, and more than 20 companies have adopted Couler as their default workflow engine interface.

Please see the following sections for installation guide and examples.

## Installation

* Couler currently only supports Argo Workflows. Please see instructions [here](https://argoproj.github.io/argo-workflows/quick-start/#install-argo-workflows)
to install Argo Workflows on your Kubernetes cluster.
* Install Python 3.6+
* Install Couler Python SDK via the following command:

```bash
python3 -m pip install git+https://github.com/couler-proj/couler --ignore-installed
```
Alternatively, you can clone this repository and then run the following to install:

```bash
python setup.py install
```

## Try Couler with Argo Workflows

Click [here](https://katacoda.com/argoproj/courses/argo-workflows/python) to launch the interactive Katacoda environment and learn how to write and submit your first Argo workflow using Couler Python SDK in your browser!

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


def job(name):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[name],
        step_name=name,
    )


#     A
#    / \
#   B   C
#  /
# D
def linear():
    couler.set_dependencies(lambda: job(name="A"), dependencies=None)
    couler.set_dependencies(lambda: job(name="B"), dependencies=["A"])
    couler.set_dependencies(lambda: job(name="C"), dependencies=["A"])
    couler.set_dependencies(lambda: job(name="D"), dependencies=["B"])

#   A
#  / \
# B   C
#  \ /
#   D
def diamond():
    couler.dag(
        [
            [lambda: job(name="A")],
            [lambda: job(name="A"), lambda: job(name="B")],  # A -> B
            [lambda: job(name="A"), lambda: job(name="C")],  # A -> C
            [lambda: job(name="B"), lambda: job(name="D")],  # B -> D
            [lambda: job(name="C"), lambda: job(name="D")],  # C -> D
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

* [Introducing Couler: Unified Interface for Constructing and Managing Workflows, Argo Workflows Community Meeting](https://docs.google.com/presentation/d/11KVEkKQGeV3R_-nHdqlzQV2uOrya94ra6Ilm_k6RwE4/edit?usp=sharing)
* [Authoring and Submitting Argo Workflows using Python](https://blog.argoproj.io/authoring-and-submitting-argo-workflows-using-python-aff9a070d95f)

## Citation

Please cite the repo if you use the code in this repo.
```bibtex
@misc{Couler,
  author = {Xiaoda Wang, Yuan Tang, Tengda Guo, Bo Sang, Jingji Wu, Jian Sha, Ke Zhang, Jiang Qian, Mingjie Tang},
  title = {Couler: Unified Machine Learning Workflow Optimization in Cloud},
  year = {2023},
  publisher = {GitHub},
  howpublished = {\url{https://github.com/couler-proj/couler/tree/master/docs/Technical-Report-of-Couler}}.
}
```
