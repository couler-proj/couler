from collections import OrderedDict

import couler.core.pyfunc as pyfunc


class Artifact(object):
    def __init__(self, path, type=None, is_global=False):
        # TODO (terrytangyuan): This seems hacky.
        #   If line number changes, we need to update tests as well.
        _, caller_line = pyfunc.invocation_location()
        self.id = "output-id-%s" % caller_line
        self.path = path
        # TODO (terrytangyuan): this is not used for now and we currently
        #   only support "valueFrom".
        self.type = type
        self.is_global = is_global

    def to_yaml(self):
        yaml_output = OrderedDict(
            {"name": self.id, "valueFrom": {"path": self.path}}
        )
        if self.is_global:
            yaml_output["globalName"] = "global-" + self.id
        return yaml_output


class OssArtifact(Artifact):
    """
    OssArtifact build the mapping from local path to remote oss bucekt,
    user can read/write data from OSS as read/write local file
    """

    def __init__(
        self,
        path,
        accesskey_id,
        accesskey_secret,
        bucket,
        key=None,
        endpoint="http://oss-cn-hangzhou-zmf.aliyuncs.com",
        is_global=False,
    ):
        self.id = "output-oss-%s" % pyfunc._get_uuid()
        # path is used for local path
        self.path = path
        self.type = "OSS"
        self.is_global = is_global

        if accesskey_secret is None or accesskey_id is None or bucket is None:
            raise SyntaxError("need to input the correct config for oss")

        self.bucket = bucket

        if key is None:
            # assume the local path is the same as the path of OSS
            self.key = path
        else:
            self.key = key

        self.endpoint = endpoint

        import couler.argo as couler

        secrets = {"accessKey": accesskey_id, "secretKey": accesskey_secret}
        # TODO: check this secret exist or not
        self.secret = couler.create_secret(secrets)

    def to_yaml(self):
        oss_config = OrderedDict(
            {
                "endpoint": self.endpoint,
                "bucket": self.bucket,
                "key": self.key,
                "accessKeySecret": {"name": self.secret, "key": "accessKey"},
                "secretKeySecret": {"name": self.secret, "key": "secretKey"},
            }
        )
        yaml_output = OrderedDict(
            {"name": self.id, "path": self.path, "oss": oss_config}
        )
        if self.is_global:
            yaml_output["globalName"] = "global-" + self.id
        return yaml_output
