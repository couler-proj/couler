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

After installing Couler, run the hello world example to submit your first workflow:

```python
--8<-- "examples/hello_world.py"
```

Once the workflow is successfully submitted, the following logs will be shown:

```
INFO:root:Found local kubernetes config. Initialized with kube_config.
INFO:root:Checking workflow name/generatedName runpy-
INFO:root:Submitting workflow to Argo
INFO:root:Workflow runpy-ddc2m has been submitted in "default" namespace!
```
