# Copyright 2021 The Couler Authors. All rights reserved.
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
import logging
import os
import re
import tempfile

import pyaml
import yaml
from kubernetes import client as k8s_client
from kubernetes import config

from couler.core.constants import CronWorkflowCRD, WorkflowCRD

_SUBMITTER_IMPL_ENV_VAR_KEY = "SUBMITTER_IMPLEMENTATION"


class _SubmitterImplTypes(object):
    PYTHON = "Python"
    GO = "Go"


# TODO: some k8s common parts can move to another file later.
class ArgoSubmitter(object):
    """A submitter which submits a workflow to Argo"""

    def __init__(
        self,
        namespace="default",
        config_file=None,
        context=None,
        client_configuration=None,
        persist_config=True,
    ):
        logging.basicConfig(level=logging.INFO)
        self.namespace = namespace
        self.go_impl = (
            os.environ.get(
                _SUBMITTER_IMPL_ENV_VAR_KEY, _SubmitterImplTypes.PYTHON
            )
            == _SubmitterImplTypes.GO
        )
        if self.go_impl:
            from ctypes import c_char_p, cdll
            from couler.core.proto_repr import get_default_proto_workflow

            self.go_submitter = cdll.LoadLibrary("./submit.so")
            self.go_submitter.Submit.argtypes = [c_char_p, c_char_p, c_char_p]
            self.go_submitter.Submit.restype = c_char_p

            with tempfile.NamedTemporaryFile(
                dir="/tmp", delete=False, mode="wb"
            ) as tmp_file:
                self.proto_path = tmp_file.name
                proto_wf = get_default_proto_workflow()
                tmp_file.write(proto_wf.SerializeToString())
        else:
            try:
                config.load_kube_config(
                    config_file, context, client_configuration, persist_config
                )
                logging.info(
                    "Found local kubernetes config. "
                    "Initialized with kube_config."
                )
            except Exception:
                logging.info(
                    "Cannot find local k8s config. "
                    "Trying in-cluster config."
                )
                config.load_incluster_config()
                logging.info("Initialized with in-cluster config.")

            self._custom_object_api_client = k8s_client.CustomObjectsApi()
            self._core_api_client = k8s_client.CoreV1Api()

    @staticmethod
    def check_name(name):
        """Check the name is valid or not"""
        if len(name) > WorkflowCRD.NAME_MAX_LENGTH:
            raise ValueError(
                "Name is too long. Max length: {}, now: {}"
                "".format(WorkflowCRD.NAME_MAX_LENGTH, len(name))
            )
        if "." in name:
            raise ValueError("Name cannot include dot.")
        if "_" in name:
            raise ValueError("Name cannot include underscore.")

        match_obj = re.match(WorkflowCRD.NAME_PATTERN, name)
        if not match_obj:
            raise ValueError(
                "Name is invalid. Regex used for validation is %s"
                % WorkflowCRD.NAME_PATTERN
            )

    def get_custom_object_api_client(self):
        return self._custom_object_api_client

    def get_core_api_client(self):
        return self._core_api_client

    def submit(self, workflow_yaml, secrets=None):
        wf_name = (
            workflow_yaml["metadata"]["name"]
            if "name" in workflow_yaml["metadata"]
            else workflow_yaml["metadata"]["generateName"]
        )
        if self.go_impl:
            resp = self.go_submitter.Submit(
                self.proto_path.encode("utf-8"),
                self.namespace.encode("utf-8"),
                wf_name.encode("utf-8"),
            )
            logging.info("Response: %s" % resp.decode("utf-8"))
        else:
            if secrets:
                for secret in secrets:
                    self._create_secret(secret.to_yaml())
            logging.info("Checking workflow name/generatedName %s" % wf_name)
            self.check_name(wf_name)
            return self._create_workflow(workflow_yaml)

    def _create_workflow(self, workflow_yaml):
        yaml_str = pyaml.dump(workflow_yaml)
        workflow_yaml = yaml.safe_load(yaml_str)
        logging.info("Submitting workflow to Argo")
        try:
            response = self._custom_object_api_client.create_namespaced_custom_object(  # noqa: E501
                WorkflowCRD.GROUP,
                WorkflowCRD.VERSION,
                self.namespace,
                WorkflowCRD.PLURAL
                if workflow_yaml["kind"] == WorkflowCRD.KIND
                else CronWorkflowCRD.PLURAL,
                workflow_yaml,
            )
            logging.info(
                'Workflow %s has been submitted in "%s" namespace!'
                % (response.get("metadata", {}).get("name"), self.namespace)
            )
            return response
        except Exception as e:
            logging.error("Failed to submit workflow")
            raise e

    def _create_secret(self, secret_yaml):
        yaml_str = pyaml.dump(secret_yaml)
        secret_yaml = yaml.safe_load(yaml_str)
        return self._core_api_client.create_namespaced_secret(  # noqa: E501
            self.namespace, secret_yaml
        )
