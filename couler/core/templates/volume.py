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


class Volume(object):
    def __init__(self, name, claim_name):
        self.name = name
        self.claim_name = claim_name

    def to_dict(self):
        return OrderedDict(
            {
                "name": self.name,
                "persistentVolumeClaim": {"claimName": self.claim_name},
            }
        )


class VolumeMount(object):
    def __init__(self, name, mount_path):
        self.name = name
        self.mount_path = mount_path

    def to_dict(self):
        return OrderedDict({"name": self.name, "mountPath": self.mount_path})
