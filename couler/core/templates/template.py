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

from couler.core import utils


class Template(object):
    def __init__(
        self,
        name,
        output=None,
        input=None,
        timeout=None,
        retry=None,
        pool=None,
        enable_ulogfs=True,
        daemon=False,
        cache=None,
    ):
        self.name = name
        self.output = output
        self.input = input
        self.timeout = timeout
        self.retry = retry
        self.pool = pool
        self.enable_ulogfs = enable_ulogfs
        self.daemon = daemon
        self.cache = cache

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
        return template
