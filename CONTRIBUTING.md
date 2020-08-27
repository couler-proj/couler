# Contributing Guide

Welcome to Couler's contributing guide!

## Install Dependencies

You can install all the dependent Python packages for development via the following:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
``` 

## Run Unit Tests

You can execute all the unit tests via the following command:

```bash
python setup.py install
python -m pytest
```

## Run Integration Tests

The current integration test suite requires [Minikube](https://kubernetes.io/docs/setup/learning-environment/minikube/) and [Argo Workflows](https://argoproj.github.io/argo).
Please see instructions [here](https://kubernetes.io/docs/tasks/tools/install-minikube/) for setting up Minikube locally and instructions [here](https://argoproj.github.io/argo/quick-start/#install-argo-workflows) for installing Argo Workflows on your local Minikube cluster.

Once these are installed, execute the integration test suite in [integration_tests](integration_tests) with Python, which will be
submitting workflows to your local Minikube cluster. You can then validate workflow statuses via the following:

```bash
for WF_NAME in $(kubectl -n argo get workflows --no-headers -o custom-columns=":metadata.name")
do
    bash scripts/validate_workflow_statuses.sh ${WF_NAME}
done
```

## Run Sanity Checks

We use [pre-commit](https://github.com/pre-commit/pre-commit) to check issues on code style and quality. For example, it
runs [black](https://github.com/psf/black) for automatic Python code formatting which should fix most of the issues automatically.
You can execute the following command to run all the sanity checks:

```bash
pre-commit run --all
```

## Sign the Contributor License Agreement (CLA)

If you haven't signed the CLA yet, [@CLAassistant](https://github.com/CLAassistant) will notify you on your pull request.
Then you can simply follow the provided instructions on the pull request and sign the CLA using your GitHub account.

For your convenience, the content of the CLA can be found [here](https://gist.github.com/terrytangyuan/806ec0627ec54cdf92512936996da986).
