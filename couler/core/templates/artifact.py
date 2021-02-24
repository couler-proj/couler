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

from couler import argo as couler
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
        accesskey_id=None,
        accesskey_secret=None,
        bucket=None,
        key=None,
        endpoint="",
        is_global=False,
    ):
        self.type = artifact_type
        self.id = f"output-{self.type}-{utils._get_uuid()}"
        # path is used for local path
        self.path = path
        self.is_global = is_global
        self.bucket = bucket
        self.key = key
        self.endpoint = endpoint

        if accesskey_id and accesskey_secret:
            secret = {"accessKey": accesskey_id, "secretKey": accesskey_secret}
            # TODO: check this secret exist or not
            self.secret = couler.create_secret(secret)
        else:
            self.secret = None

    def to_yaml(self):
        config = OrderedDict()
        if self.key is not None:
            config.update({"key": self.key})
        if self.secret is not None:
            config.update(
                {
                    "accessKeySecret": {
                        "name": self.secret,
                        "key": "accessKey",
                    },
                    "secretKeySecret": {
                        "name": self.secret,
                        "key": "secretKey",
                    },
                }
            )
        if self.bucket is not None:
            config.update({"bucket": self.bucket})
        if self.endpoint:
            config.update({"endpoint": self.endpoint})
        yaml_output = (
            OrderedDict(
                {"name": self.id, "path": self.path, self.type: config}
            )
            if self.type != couler.ArtifactType.LOCAL
            else {"name": self.id, "path": self.path}
        )
        if self.is_global:
            yaml_output["globalName"] = "global-" + self.id
        return yaml_output


class LocalArtifact(TypedArtifact):
    def __init__(self, path, is_global=False):
        super().__init__(
            couler.ArtifactType.LOCAL, path=path, is_global=is_global
        )


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
            couler.ArtifactType.S3,
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
            couler.ArtifactType.OSS,
            path,
            accesskey_id,
            accesskey_secret,
            bucket,
            key,
            endpoint,
            is_global,
        )
