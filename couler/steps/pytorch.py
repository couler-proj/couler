import copy
import uuid

import pyaml

import couler.argo as couler
from couler.core import utils
from couler.steps.pod_utils import _generate_pod_spec

pod_types = {"Master", "Worker"}

container_template = {"name": "pytorch", "image": "", "command": ""}

pod_template = {
    "replicas": 1,
    "restartPolicy": "",
    "template": {"spec": {"containers": []}},
}

manifest_template = {
    "apiVersion": '"kubeflow.org/v1"',
    "kind": '"PyTorchJob"',
    "metadata": {"name": ""},
    "spec": {"cleanPodPolicy": "", "pytorchReplicaSpecs": {}},
}


def train(
    image=None,
    command="",
    secret=None,
    master_image=None,
    master_resources=None,
    master_restart_policy="Never",
    master_command=None,
    num_workers=0,
    worker_image=None,
    worker_resources=None,
    worker_restart_policy="Never",
    worker_command=None,
    clean_pod_policy="Running",
    timeout=None,
):
    name = "pytorch-train-%s" % str(uuid.uuid4())
    success_condition = (
        "status.replicaStatuses.Worker.succeeded == %s" % num_workers
    )
    failure_condition = "status.replicaStatuses.Worker.failed > 0"

    manifest = copy.deepcopy(manifest_template)
    manifest["metadata"].update({"name": name})
    manifest["spec"].update({"cleanPodPolicy": clean_pod_policy})

    master_image = master_image if master_image else image
    master_command = master_command if master_command else command

    master_pod = _generate_pod_spec(
        pod_template,
        container_template,
        allowed_pod_types=pod_types,
        pod_type="Master",
        image=master_image,
        replicas=1,
        secret=secret,
        command=master_command,
        resources=master_resources,
        restart_policy=master_restart_policy,
    )

    manifest["spec"]["pytorchReplicaSpecs"].update({"Master": master_pod})

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
            restart_policy=worker_restart_policy,
        )

        manifest["spec"]["pytorchReplicaSpecs"].update({"Worker": worker_pod})

    step_name, _ = utils.invocation_location()

    couler.run_job(
        manifest=pyaml.dump(manifest),
        success_condition=success_condition,
        failure_condition=failure_condition,
        step_name=step_name,
        timeout=timeout,
    )
