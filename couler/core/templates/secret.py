import hashlib
import json
from collections import OrderedDict

from couler import pyfunc


class Secret(object):
    def __init__(self, namespace, data):

        if not isinstance(data, dict):
            raise TypeError("The secret data is required to be a dict")
        if not data:
            raise ValueError("The secret data is empty")

        self.namespace = namespace
        # TO avoid create duplicate secret
        cypher_md5 = hashlib.md5(
            json.dumps(data, sort_keys=True).encode("utf-8")
        ).hexdigest()
        self.name = "couler-%s" % cypher_md5

        self.data = {k: pyfunc.encode_base64(v) for k, v in data.items()}

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
