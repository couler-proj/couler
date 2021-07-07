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

import attr

from couler.core import utils


@attr.s
class Template(object):
    name = attr.ib()
    output = attr.ib(default=None)
    input = attr.ib(default=None)
    timeout = attr.ib(default=None)
    retry = attr.ib(default=None)
    pool = attr.ib(default=None)
    enable_ulogfs = attr.ib(default=True)
    daemon = attr.ib(default=False)
    cache = attr.ib(default=None)
    tolerations = attr.ib(default=None)


def to_dict(self):
    template = OrderedDict({"name": self.name})
    if self.daemon:
        template["daemon"] = True
    if self.timeout is not None:
        template["activeDeadlineSeconds"] = self.timeout
    if self.retry is not None:
        template["retryStrategy"] = utils.config_retry_strategy(self.retry)
    if self.cache is not None:
        template["memoize"] = self.cache.to_dict()
    if self.tolerations is not None:
        template["tolerations"] = self.tolerations.copy()
    return template
