import copy
import uuid

import pyaml

import couler.argo as couler
import couler.pyfunc as pyfunc

container_template = {"name": "tensorflow", "image": "", "command": ""}

pod_template = {
    "replicas": 1,
    "restartPolicy": "",
    "template": {"spec": {"containers": []}},
}

manifest_template = {
    "apiVersion": '"kubeflow.org/v1alpha2"',
    "kind": '"TFJob"',
    "metadata": {"name": ""},
    "spec": {"cleanPodPolicy": "", "tfReplicaSpecs": {}},
}

pod_types = {"Chief", "PS", "Worker"}


def _validate_pod_params(
    pod_type=None, image=None, replicas=0, restart_policy=None
):

    if pod_type not in pod_types:
        raise ValueError("Invalid value %s for parameter pod_type." % pod_type)
    if replicas == 0:
        raise ValueError("Parameter replicas value should be more than 0.")
    if image is None:
        raise ValueError("Parameter image should not be None.")
    if pod_type == "Chief" and replicas > 1:
        raise ValueError("Chief pod's replicas should be 1.")
    if restart_policy is None:
        raise ValueError("Parameter restart_policy should not be None.")


def _generate_pod(
    pod_type=None,
    image=None,
    replicas=0,
    secret=None,
    command="",
    resources=None,
    restart_policy=None,
):

    _validate_pod_params(
        pod_type=pod_type,
        image=image,
        replicas=replicas,
        restart_policy=restart_policy,
    )

    container = copy.deepcopy(container_template)
    container.update({"image": image, "command": command})

    if secret is not None:
        secret_envs = couler.states._secrets[secret].to_env_list()

        if "env" not in container.keys():
            container["env"] = secret_envs
        else:
            container["env"].extend(secret_envs)

    if resources is not None:
        # User-defined resource, should be formatted like
        # "cpu=1,memory=1024,disk=2048,gpu=1,gpu_type=p100,shared_memory=20480"
        try:
            kvs = resources.split(",")
            print(kvs)
            limits = {}
            for kv in kvs:
                k, v = kv.split("=")
                if k in ["gpu", "memory", "disk", "shared_memory"]:
                    v = int(v)
                elif k == "cpu":
                    v = float(v)

                limits[k] = v

            resource_limits = {"limits": limits}
            container["resources"] = resource_limits

        except Exception:
            raise Exception("Unrecognized resource type %s" % resources)

    pod = copy.deepcopy(pod_template)
    pod.update({"replicas": replicas, "restartPolicy": restart_policy})
    pod["template"]["spec"]["containers"].append(container)

    return pod


def train(
    image=None,
    command="",
    secret=None,
    no_chief=True,
    chief_image=None,
    chief_resources=None,
    chief_restart_policy="Never",
    chief_command=None,
    num_ps=0,
    ps_image=None,
    ps_resources=None,
    ps_restart_policy="Never",
    ps_command=None,
    num_workers=0,
    worker_image=None,
    worker_resources=None,
    worker_restart_policy="Never",
    worker_command=None,
    clean_pod_policy="Running",
    timeout=None,
):
    name = "tf-train-%s" % str(uuid.uuid4())
    success_condition = "status.tfReplicaStatuses.Worker.succeeded > 0"
    failure_condition = "status.tfReplicaStatuses.Worker.failed > 0"

    manifest = copy.deepcopy(manifest_template)
    manifest["metadata"].update({"name": name})
    manifest["spec"].update({"cleanPodPolicy": clean_pod_policy})

    if not no_chief:
        chief_image = chief_image if chief_image else image
        chief_command = chief_command if chief_command else command

        chief_pod = _generate_pod(
            pod_type="Chief",
            image=chief_image,
            replicas=1,
            secret=secret,
            command=chief_command,
            resources=chief_resources,
            restart_policy=chief_restart_policy,
        )

        manifest["spec"]["tfReplicaSpecs"].update({"Chief": chief_pod})

    if num_ps > 0:
        ps_image = ps_image if ps_image else image
        ps_command = ps_command if ps_command else command

        ps_pod = _generate_pod(
            pod_type="PS",
            image=ps_image,
            replicas=num_ps,
            secret=secret,
            command=ps_command,
            resources=ps_resources,
            restart_policy=ps_restart_policy,
        )

        manifest["spec"]["tfReplicaSpecs"].update({"PS": ps_pod})

    if num_workers > 0:
        worker_image = worker_image if worker_image else image
        worker_command = worker_command if worker_command else command

        worker_pod = _generate_pod(
            pod_type="Worker",
            image=worker_image,
            replicas=num_workers,
            secret=secret,
            command=worker_command,
            resources=worker_resources,
            restart_policy=worker_restart_policy,
        )

        manifest["spec"]["tfReplicaSpecs"].update({"Worker": worker_pod})

    step_name, _ = pyfunc.invocation_location()

    couler.run_job(
        manifest=pyaml.dump(manifest),
        success_condition=success_condition,
        failure_condition=failure_condition,
        step_name=step_name,
        timeout=timeout,
    )
