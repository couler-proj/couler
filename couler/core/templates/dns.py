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


class DnsConfig(object):
    def __init__(self, nameservers=None, options=None, searches=None):
        self.nameservers = nameservers
        self.options = options
        self.searches = searches

    def to_dict(self):
        dt = OrderedDict()
        if utils.non_empty(self.nameservers):
            dt.update({"nameservers": self.nameservers})
        if utils.non_empty(self.options):
            dt.update({"options": self.get_options_to_dict()})
        if utils.non_empty(self.searches):
            dt.update({"searches": self.searches})
        return dt

    def get_options_to_dict(self):
        t = []
        for option in self.options:
            t.append(option.to_dict())
        return t


class DnsConfigOption(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def to_dict(self):
        return OrderedDict({"name": self.name, "value": self.value})
