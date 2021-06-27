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
import attr
from stringcase import spinalcase


@attr.s
class Parameter(object):
    name: str = attr.ib(converter=spinalcase)
    value = attr.ib()
    context: str = attr.ib(default=None)

    def to_dict(self):
        return {"name": self.name, "value": self.value}

    @property
    def placeholder(self):
        return "{{{0}.parameters.{1}}}".format(self.context, self.name)

    @property
    def escaped_placeholder(self):
        return '"{0}"'.format(self.placeholder)


@attr.s
class InputParameter(Parameter):
    def __attrs_post_init__(self):
        self.context = "inputs"

    def to_dict(self):
        return {"name": self.name}


@attr.s
class ArgumentsParameter(Parameter):
    def __attrs_post_init__(self):
        self.context = "arguments"


# @attr.s
# class ParameterArtifact(Parameter):
#     path: str = attr.ib()
#     artifact: str = attr.ib()
#     type: str = attr.ib()
#
#     def to_dict(self):
#         return super().to_dict().update({
#             "path": self.path,
#             "artifact": self.artifact,
#             "type": self.type,
#         })
