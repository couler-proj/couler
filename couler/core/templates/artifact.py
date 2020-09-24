# Copyright 2020 The Couler Authors. All rights reserved.
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

from couler.core import utils


class Artifact(object):
    def __init__(self, path, type=None, is_global=False):
        # TODO (terrytangyuan): This seems hacky.
        #   If line number changes, we need to update tests as well.
        _, caller_line = utils.invocation_location()
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


class TypedArtifact(Artifact):
    """
    TypedArtifact builds the mapping from local path to a remote bucket.

    A user can read/write data from a remote bucket in the same way they
    write to a local file.
    """

    def __init__(
        self,
        artifact_type,
        path,
        accesskey_id,
        accesskey_secret,
        bucket,
        key=None,
        endpoint="",
        is_global=False,
    ):
        self.type = artifact_type
        self.id = f"output-{self.type}-{utils._get_uuid()}"
        # path is used for local path
        self.path = path

        self.is_global = is_global

        if accesskey_secret is None or accesskey_id is None or bucket is None:
            raise SyntaxError(
                f"need to input the correct config for {self.type}"
            )

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
        config = OrderedDict(
            {
                "endpoint": self.endpoint,
                "bucket": self.bucket,
                "key": self.key,
                "accessKeySecret": {"name": self.secret, "key": "accessKey"},
                "secretKeySecret": {"name": self.secret, "key": "secretKey"},
            }
        )
        yaml_output = OrderedDict(
            {"name": self.id, "path": self.path, self.type: config}
        )
        if self.is_global:
            yaml_output["globalName"] = "global-" + self.id
        return yaml_output


class S3Artifact(TypedArtifact):
    def __init__(
        self,
        path,
        accesskey_id,
        accesskey_secret,
        bucket,
        key=None,
        endpoint="s3.amazonaws.com",
        is_global=False,
    ):
        super().__init__(
            "s3",
            path,
            accesskey_id,
            accesskey_secret,
            bucket,
            key,
            endpoint,
            is_global,
        )


class OssArtifact(TypedArtifact):
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
        super().__init__(
            "oss",
            path,
            accesskey_id,
            accesskey_secret,
            bucket,
            key,
            endpoint,
            is_global,
        )
