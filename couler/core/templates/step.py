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
from couler.core.templates import OutputParameter
from couler.core.templates.template import Template


@attr.s
class Step(object):
    name = attr.ib()
    template = attr.ib(default=None)
    arguments = attr.ib(default=None)
    with_items = attr.ib(default=None)
    with_param = attr.ib(default=None)
    parallelism = attr.ib(default=None)
    when = attr.ib(default=None)

    def to_dict(self):
        d = OrderedDict({"name": self.name})
        if self.template is not None:
            d.update({"template": self.template})
        if self.when is not None:
            d.update({"when": self.when})
        if utils.non_empty(self.arguments):
            d.update({"arguments": self.arguments})
        if utils.non_empty(self.with_items):
            d.update({"withItems": self.with_items})
        if utils.non_empty(self.with_param):
            if isinstance(self.with_param, OutputParameter):
                d.update({"withParam": self.with_param.placeholder("steps")})
            else:
                raise ValueError("argument for withParam must be a parameter.")
        if utils.non_empty(self.parallelism):
            d.update({"parallelism": self.parallelism})
        return d


class Steps(Template):
    def __init__(self, name, steps=None):
        Template.__init__(self, name=name)
        self.steps = steps

    def to_dict(self):
        template = Template.to_dict(self)
        template["steps"] = self.steps
        return template
