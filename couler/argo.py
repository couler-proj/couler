# Copyright 2020 The Couler Authors. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import atexit
import logging

import pyaml
import yaml
from kubernetes import client as k8s_client
from kubernetes import config

from couler.argo_submitter import ArgoSubmitter
from couler.core import states  # noqa: F401
from couler.core.config import config_workflow  # noqa: F401
from couler.core.constants import *  # noqa: F401, F403
from couler.core.constants import WorkflowCRD
from couler.core.run_templates import (  # noqa: F401
    run_container,
    run_job,
    run_script,
)
from couler.core.states import (  # noqa: F401
    _cleanup,
    get_secret,
    get_step_output,
    workflow,
)
from couler.core.syntax import *  # noqa: F401, F403
from couler.core.templates import Artifact, OssArtifact, Secret  # noqa: F401
from couler.core.workflow_validation_utils import (  # noqa: F401
    validate_workflow_yaml,
)


def workflow_yaml():
    return states.workflow.to_dict()


def run(submitter=ArgoSubmitter):
    """To submit the workflow using user-provided submitter implementation.
       Note that, the provided submitter must have a submit function which
       takes the workflow YAML as input.
    """
    states._enable_print_yaml = False

    if submitter is None:
        raise ValueError("The input submitter is None")
    wf = workflow_yaml()
    secrets = states._secrets.values()
    # TODO (terrytangyuan): Decouple with Argo and then uncomment this
    # validate_workflow_yaml(wf)
    if isinstance(submitter, ArgoSubmitter):
        return submitter.submit(wf, secrets=secrets)
    elif issubclass(submitter, ArgoSubmitter):
        submitter = ArgoSubmitter()
        return submitter.submit(wf, secrets=secrets)
    else:
        raise ValueError("Only ArgoSubmitter is supported currently.")


def delete(
    name,
    namespace="default",
    config_file=None,
    context=None,
    client_configuration=None,
    persist_config=True,
    grace_period_seconds=5,
    propagation_policy="Background",
):
    try:
        config.load_kube_config(
            config_file, context, client_configuration, persist_config
        )
        logging.info(
            "Found local kubernetes config. Initialized with kube_config."
        )
    except Exception:
        logging.info("Cannot find local k8s config. Trying in-cluster config.")
        config.load_incluster_config()
        logging.info("Initialized with in-cluster config.")

    api_client = k8s_client.CustomObjectsApi()
    delete_body = k8s_client.V1DeleteOptions(
        grace_period_seconds=grace_period_seconds,
        propagation_policy=propagation_policy,
    )
    try:
        return api_client.delete_namespaced_custom_object(
            WorkflowCRD.GROUP,
            WorkflowCRD.VERSION,
            namespace,
            WorkflowCRD.PLURAL,
            name,
            body=delete_body,
        )
    # TODO (terrytangyuan): `ApiException` seems unavailable in
    #  some versions of k8s client.
    except k8s_client.api_client.ApiException as e:
        raise Exception("Exception when deleting the workflow: %s\n" % e)


def init_yaml_dump():
    yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str

    def repr_str(dumper, data):
        if "\n" in data:
            return dumper.represent_scalar(
                u"tag:yaml.org,2002:str", data, style="|"
            )
        return dumper.org_represent_str(data)

    yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)


def _dump_yaml():
    yaml_str = pyaml.dump(workflow_yaml())

    # The maximum size of an etcd request is 1.5MiB:
    # https://github.com/etcd-io/etcd/blob/master/Documentation/dev-guide/limit.md#request-size-limit # noqa: E501
    if len(yaml_str) > 1573000:
        raise ValueError(
            "The size of workflow YAML file should not be more \
            than 1.5MiB."
        )

    # TODO(weiyan): add unittest for verifying multiple secrets outputs
    for secret in states._secrets.values():
        yaml_str += "\n---\n" + pyaml.dump(secret.to_yaml())

    if states._enable_print_yaml:
        print(yaml_str)


def create_parameter_artifact(path, is_global=False):
    return Artifact(path=path, type="parameters", is_global=is_global)


def create_oss_artifact(
    path,
    bucket=None,
    accesskey_id=None,
    accesskey_secret=None,
    key=None,
    endpoint=None,
    is_global=False,
):
    """
    Configure the object as OssArtifact
    OSS configuration can be found
    (https://www.alibabacloud.com/help/doc-detail/32027.htm)
    :param path: the local path of container
    :param bucket: oss bucket
    :param accesskey_id: oss user id
    :param accesskey_secret: oss user ky
    :param key: key of oss object
    :param endpoint: end point of oss
    :return:
    """
    return OssArtifact(
        path,
        accesskey_id,
        accesskey_secret,
        bucket,
        key=key,
        endpoint=endpoint,
        is_global=is_global,
    )


# TODO: why we use "default" namespace here?
def create_secret(secret_data={}, namespace="default"):
    """Store the input dict as a secret in k8s, and return the secret name."""
    secret = Secret(namespace=namespace, data=secret_data)

    # avoid create the secret for same input dict
    if secret.name not in states._secrets:
        states._secrets[secret.name] = secret

    return secret.name


# Dump the YAML when exiting
init_yaml_dump()
atexit.register(_dump_yaml)
