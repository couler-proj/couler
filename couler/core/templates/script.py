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

from couler.core import states, utils
from couler.core.constants import OVERWRITE_GPU_ENVS
from couler.core.templates.secret import Secret
from couler.core.templates.container import Container


class Script(Container):
    def __init__(
        self,
        name,
        image,
        command,
        source,
        args=None,
        env=None,
        secret=None,
        resources=None,
        image_pull_policy=None,
        retry=None,
        timeout=None,
        pool=None,
        output=None,
        input=None,
        enable_ulogfs=True,
        daemon=False,
        volume_mounts=None,
        working_dir=None,
        node_selector=None,
        volumes=None,
    ):
        Container.__init__(
            self,
            name,
            image,
            command,
            args=args,
            env=env,
            secret=secret,
            resources=resources,
            image_pull_policy=image_pull_policy,
            retry=retry,
            timeout=timeout,
            pool=pool,
            output=output,
            input=input,
            enable_ulogfs=enable_ulogfs,
            daemon=daemon,
            volume_mounts=volume_mounts,
            working_dir=working_dir,
            node_selector=node_selector,
            volumes=volumes,
        )
        self.source = source

    def to_dict(self):
        template = Container.to_dict(self)
        template.pop("container", None)
        template["script"] = self.script_dict()
        return template

    def script_dict(self):
        script = OrderedDict({"image": self.image, "command": self.command})
        script["source"] = (
            utils.body(self.source)
            if len(self.command) > 0 and self.command[0].lower() == "python"
            else self.source
        )
        return script
