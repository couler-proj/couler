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

The current integration test suite requires:

- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/)

Star a k8s cluster using minikube:

```sh
minikube config set vm-driver docker
minikube config set kubernetes-version 1.18.3
minikube start
```

Install Argo Workflows:

```sh
kubectl create ns argo
kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo/v2.11.1/manifests/quick-start-minimal.yaml
```

Run the integration tests:
```sh
scripts/integration_tests.sh
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
