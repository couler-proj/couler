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

import couler.argo as couler


def _validate_pod_params(pod_type, allowed_pod_types, image=None, replicas=0):

    if pod_type not in allowed_pod_types:
        raise ValueError("Invalid value %s for parameter pod_type." % pod_type)
    if replicas == 0:
        raise ValueError("Parameter replicas value should be more than 0.")
    if image is None:
        raise ValueError("Parameter image should not be None.")
    if pod_type in ["Master", "Chief", "Launcher"] and replicas > 1:
        raise ValueError("Master/Chief/Launcher pod's replicas should be 1.")


def _generate_pod_spec(
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
    pod.update({"replicas": replicas})
    if restart_policy is not None:
        pod.update({"restartPolicy": restart_policy})
    pod["template"]["spec"]["containers"].append(container)

    return pod
