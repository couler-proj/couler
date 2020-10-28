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

import copy
from collections import OrderedDict

from couler.core import utils
from couler.core.templates.secret import Secret
from couler.core.templates.template import Template


class Script(Template):
    def __init__(
        self,
        name,
        image,
        command,
        source,
        env=None,
        secret=None,
        resources=None,
        image_pull_policy=None,
        retry=None,
        timeout=None,
        pool=None,
        daemon=False,
    ):
        Template.__init__(
            self,
            name=name,
            timeout=timeout,
            retry=retry,
            pool=pool,
            daemon=daemon,
        )
        self.image = image
        self.command = "python" if command is None else command
        self.source = source
        self.env = env
        self.secret = secret
        self.resources = resources
        self.image_pull_policy = image_pull_policy

    def to_dict(self):
        template = Template.to_dict(self)
        template["script"] = self.script_dict()
        return template

    def script_dict(self):
        script = OrderedDict({"image": self.image, "command": [self.command]})
        script["source"] = (
            utils.body(self.source)
            if self.command.lower() == "python"
            else self.source
        )
        if utils.non_empty(self.env):
            script["env"] = utils.convert_dict_to_env_list(self.env)

        if self.secret is not None:
            if not isinstance(self.secret, Secret):
                raise ValueError(
                    "Parameter secret should be an instance of Secret"
                )
            if self.env is None:
                script["env"] = self.secret.to_env_list()
            else:
                script["env"].extend(self.secret.to_env_list())

        if self.resources is not None:
            script["resources"] = {
                "requests": self.resources,
                # To fix the mojibake issue when dump yaml for one object
                "limits": copy.deepcopy(self.resources),
            }
        if self.image_pull_policy is not None:
            script["imagePullPolicy"] = utils.config_image_pull_policy(
                self.image_pull_policy
            )
        return script
