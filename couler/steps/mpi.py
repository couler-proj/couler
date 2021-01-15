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

import copy
import uuid

import pyaml

import couler.argo as couler
from couler.core import utils
from couler.steps.pod_utils import _generate_pod_spec

pod_types = {"Launcher", "Worker"}

container_template = {"name": "mpi", "image": "", "command": ""}

pod_template = {"replicas": 1, "template": {"spec": {"containers": []}}}

manifest_template = {
    "apiVersion": '"kubeflow.org/v1"',
    "kind": '"MPIJob"',
    "metadata": {"name": ""},
    "spec": {"cleanPodPolicy": "", "slotsPerWorker": 1, "mpiReplicaSpecs": {}},
}


def train(
    image=None,
    command="",
    secret=None,
    launcher_image=None,
    launcher_resources=None,
    launcher_command=None,
    num_workers=0,
    worker_image=None,
    worker_resources=None,
    worker_command=None,
    clean_pod_policy="Running",
    timeout=None,
):
    name = "mpi-train-%s" % str(uuid.uuid4())
    success_condition = (
        "status.replicaStatuses.Worker.succeeded == %s" % num_workers
    )
    failure_condition = "status.replicaStatuses.Worker.failed > 0"

    manifest = copy.deepcopy(manifest_template)
    manifest["metadata"].update({"name": name})
    manifest["spec"].update({"cleanPodPolicy": clean_pod_policy})

    launcher_image = launcher_image if launcher_image else image
    launcher_command = launcher_command if launcher_command else command

    launcher_pod = _generate_pod_spec(
        pod_template,
        container_template,
        allowed_pod_types=pod_types,
        pod_type="Launcher",
        image=launcher_image,
        replicas=1,
        secret=secret,
        command=launcher_command,
        resources=launcher_resources,
    )

    manifest["spec"]["mpiReplicaSpecs"].update({"Launcher": launcher_pod})

    if num_workers > 0:
        worker_image = worker_image if worker_image else image
        worker_command = worker_command if worker_command else command

        worker_pod = _generate_pod_spec(
            pod_template,
            container_template,
            allowed_pod_types=pod_types,
            pod_type="Worker",
            image=worker_image,
            replicas=num_workers,
            secret=secret,
            command=worker_command,
            resources=worker_resources,
        )

        manifest["spec"]["mpiReplicaSpecs"].update({"Worker": worker_pod})

    step_name, _ = utils.invocation_location()

    couler.run_job(
        manifest=pyaml.dump(manifest),
        success_condition=success_condition,
        failure_condition=failure_condition,
        step_name=step_name,
        timeout=timeout,
    )
