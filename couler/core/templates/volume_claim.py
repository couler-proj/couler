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
from typing import List


class VolumeClaimTemplate(object):
    def __init__(
        self,
        claim_name: str,
        access_modes: List[str] = ["ReadWriteOnce"],
        size: str = "1Gi",
    ):
        self.claim_name = claim_name
        self.access_modes = access_modes
        self.size = size

    def to_dict(self):
        return OrderedDict(
            {
                "metadata": {"name": self.claim_name},
                "spec": {
                    "accessModes": self.access_modes,
                    "resources": {"requests": {"storage": self.size}},
                },
            }
        )
