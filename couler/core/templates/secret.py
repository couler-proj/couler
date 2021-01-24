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

import hashlib
import json
from collections import OrderedDict

from couler.core import utils


class Secret(object):
    def __init__(self, namespace, data, name=None, dry_run=False):

        if not isinstance(data, dict):
            raise TypeError("The secret data is required to be a dict")
        if not data:
            raise ValueError("The secret data is empty")

        self.namespace = namespace
        # TO avoid create duplicate secret
        cypher_md5 = hashlib.md5(
            json.dumps(data, sort_keys=True).encode("utf-8")
        ).hexdigest()
        if name is None:
            self.name = "couler-%s" % cypher_md5
        else:
            self.name = name

        self.data = {k: utils.encode_base64(v) for k, v in data.items()}
        self.dry_run = dry_run

    def to_yaml(self):
        """Covert the secret to a secret CRD specification."""
        d = OrderedDict(
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {"name": self.name, "namespace": self.namespace},
                "type": "Opaque",
                "data": {},
            }
        )
        for k, v in self.data.items():
            d["data"][k] = v
        return d

    def to_env_list(self):
        """
        Convert the secret to an environment list, and can be attached to
        containers.
        """
        secret_envs = []
        for key, _ in self.data.items():
            secret_env = {
                "name": key,
                "valueFrom": {"secretKeyRef": {"name": self.name, "key": key}},
            }
            secret_envs.append(secret_env)
        return secret_envs
