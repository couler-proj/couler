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

from collections import OrderedDict
from inspect import getfullargspec

from couler.core import utils
from couler.core.templates import Container, Job, Script, Step, Template
from couler.core.templates.volume import Volume
from couler.core.templates.volume_claim import VolumeClaimTemplate


class Workflow(object):
    """Class that keeps workflow-related information."""

    def __init__(self, workflow_filename):
        self.generate_name = workflow_filename
        self.name = None
        self.templates = dict()
        self.steps = OrderedDict()
        self.dag_tasks = OrderedDict()
        self.exit_handler_step = OrderedDict()
        self.timeout = None
        self.clean_ttl = None
        self.dag_mode = False
        self.user_id = None
        self.cluster_config = utils.load_cluster_config()
        self.cron_config = None
        self.volumes = []
        self.pvcs = []
        self.service_account = None

    def add_template(self, template: Template):
        self.templates.update({template.name: template})

    def get_template(self, name):
        return self.templates.get(name, None)

    def add_step(self, name, step: Step):
        if name not in self.steps:
            self.steps.update({name: []})
        self.steps.get(name).append(step)

    def add_pvc_template(self, pvc: VolumeClaimTemplate):
        self.pvcs.append(pvc.to_dict())

    def has_pvc_template(self, name):
        for pvc in self.pvcs:
            if pvc['metadata']['name'] == name:
                return True
        return False

    def add_volume(self, volume: Volume):
        self.volumes.append(volume.to_dict())

    def has_volume(self, name):
        for volume in self.volumes:
            if volume['name'] == name:
                return True
        return False

    def get_step(self, name):
        return self.steps.get(name, None)

    def get_steps_dict(self):
        if len(self.steps) == 0:
            return {}
        steps_list = list()
        for step in self.steps.values():
            step_list = []
            for sub_step in step:
                step_list.append(sub_step.to_dict())
            steps_list.append(step_list)
        return steps_list

    def enable_dag_mode(self):
        self.dag_mode = True

    def dag_mode_enabled(self):
        return self.dag_mode

    def get_dag_task(self, name):
        return self.dag_tasks.get(name, None)

    def update_dag_task(self, name, task):
        self.dag_tasks.update({name: task})

    def get_cluster_config_name(self):
        return (
            None
            if self.cluster_config is None
            else self.cluster_config._cluster
        )

    def to_dict(self):
        d = OrderedDict(
            {
                "apiVersion": "argoproj.io/v1alpha1",
                "kind": "Workflow",
                "metadata": {},
            }
        )

        if self.cron_config is not None:
            d["kind"] = "CronWorkflow"

        # Metadata part
        if self.name is not None:
            d["metadata"]["name"] = self.name
            entrypoint = self.name
        else:
            d["metadata"]["generateName"] = "%s-" % self.generate_name
            entrypoint = self.generate_name
        # TODO (terrytangyuan): There is an issue when working
        #  with ArgoSubmitter.
        # if self.user_id is not None:
        #     d["metadata"]["labels"] = {"couler_job_user": self.user_id}

        workflow_spec = {"entrypoint": entrypoint}
        if self.dag_mode_enabled():
            dag = {"tasks": list(self.dag_tasks.values())}
            ts = [OrderedDict({"name": entrypoint, "dag": dag})]
        else:
            ts = [{"name": entrypoint, "steps": self.get_steps_dict()}]
        for template in self.templates.values():
            template_dict = template.to_dict()
            if (
                isinstance(template, Container)
                or isinstance(template, Job)
                or isinstance(template, Script)
            ) and self.cluster_config is not None:
                sig = getfullargspec(self.cluster_config.config_pod)
                num_args = len(sig.args)
                # This is to support cluster configuration whose
                # implementation has the following signature:
                # `config_pod(self, template)`.
                if num_args == 2:
                    template_dict = self.cluster_config.config_pod(
                        template_dict
                    )
                # This is to support old cluster configuration whose
                # implementation has the following signature:
                # `config_pod(self, template, pool, enable_ulogfs)`.
                # TODO (terrytangyuan): Remove sensitive words here.
                else:
                    # The try-except here is necessary in case the
                    # implementation of `config_pod` supports additional
                    # arguments with default values.
                    try:
                        template_dict = self.cluster_config.config_pod(
                            template_dict,
                            template.pool,
                            template.enable_ulogfs,
                        )
                    except Exception:
                        raise ValueError(
                            "Unsupported signature for cluster spec: %s" % sig
                        )
            ts.append(template_dict)
            #check volumes
            volume_mounts = template.get_volume_mounts()
            if volume_mounts is not None:
                for volume_mount in volume_mounts:
                    if self.has_pvc_template(volume_mount.name) is False and self.has_volume(volume_mount.name) is False:
                        #autogenerate emptydir volume
                        self.volumes.append(
                            {"name": volume_mount.name, "emptyDir": {}}
                        )

        if self.volumes:
            print(self.volumes)
            workflow_spec.update({"volumes": self.volumes})
        if self.pvcs:
            workflow_spec.update({"volumeClaimTemplates": self.pvcs})
        if len(self.exit_handler_step) > 0:
            workflow_spec["onExit"] = "exit-handler"
            ts.extend(
                [
                    {
                        "name": "exit-handler",
                        "steps": list(self.exit_handler_step.values()),
                    }
                ]
            )

        workflow_spec["templates"] = ts

        if self.timeout is not None:
            workflow_spec["activeDeadlineSeconds"] = self.timeout

        if self.clean_ttl is not None:
            workflow_spec["ttlSecondsAfterFinished"] = self.clean_ttl

        if self.service_account is not None:
            workflow_spec["serviceAccountName"] = self.service_account

        # Spec part
        if self.cluster_config is not None and hasattr(
            self.cluster_config, "config_workflow"
        ):
            sig = getfullargspec(self.cluster_config.config_workflow)
            # This is to support cluster configuration to modify the
            # workflow spec whose implementation has the following signature:
            # `config_workflow(self, workflow_spec)`.
            if len(sig.args) == 2:
                workflow_spec = self.cluster_config.config_workflow(
                    workflow_spec
                )
            else:
                raise ValueError(
                    "Unsupported signature for cluster spec: %s" % sig
                )
        if self.cron_config is not None:
            d["spec"] = self.cron_config
            for key, value in self.cron_config.items():
                d["spec"][key] = value
            d["spec"]["workflowSpec"] = workflow_spec
        else:
            d["spec"] = workflow_spec

        return d

    def config_cron_workflow(self, cron_config):
        self.cron_config = cron_config

    def cleanup(self):
        self.name = None
        self.timeout = None
        self.clean_ttl = None
        self.templates = dict()
        self.steps = OrderedDict()
        self.dag_tasks = OrderedDict()
        self.exit_handler_step = OrderedDict()
        self.dag_mode = False
        self.user_id = None
        self.cluster_config = None
        self.cron_config = None
        self.volumes = []
        self.pvcs = []
        self.service_account = None
