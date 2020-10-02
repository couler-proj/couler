import copy

import couler.argo as couler


def _validate_pod_params(
    pod_type, allowed_pod_types, image=None, replicas=0, restart_policy=None
):

    if pod_type not in allowed_pod_types:
        raise ValueError("Invalid value %s for parameter pod_type." % pod_type)
    if replicas == 0:
        raise ValueError("Parameter replicas value should be more than 0.")
    if image is None:
        raise ValueError("Parameter image should not be None.")
    if pod_type == "Master" and replicas > 1:
        raise ValueError("Master/Chief pod's replicas should be 1.")
    if restart_policy is None:
        raise ValueError("Parameter restart_policy should not be None.")


def _generate_pod(
    pod_template,
    container_template,
    allowed_pod_types,
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
        allowed_pod_types=allowed_pod_types,
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
