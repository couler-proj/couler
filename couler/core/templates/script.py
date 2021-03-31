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

import copy
from collections import OrderedDict

from couler.core import states, utils
from couler.core.constants import OVERWRITE_GPU_ENVS
from couler.core.templates.container import Container
from couler.core.templates.secret import Secret


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
        cache=None,
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
            cache=cache,
        )
        self.image = image
        self.command = "python" if command is None else command
        self.source = source
        self.env = env
        self.secret = secret
        self.resources = resources
        self.image_pull_policy = image_pull_policy

    def to_dict(self):
        template = Container.to_dict(self)
        if (
            not utils.gpu_requested(self.resources)
            and states._overwrite_nvidia_gpu_envs
        ):
            if self.env is None:
                self.env = {}
            self.env.update(OVERWRITE_GPU_ENVS)
        if "container" in template:
            template["script"] = template.pop("container")
        template["script"].update(self.script_dict())
        return template

    def script_dict(self):
        if isinstance(self.command, list):
            script = OrderedDict(
                {"image": self.image, "command": self.command}
            )
        else:
            script = OrderedDict(
                {"image": self.image, "command": [self.command]}
            )
        source_code_string = None
        if callable(self.source):
            source_code_string = utils.body(self.source)
        elif isinstance(self.source, str):
            source_code_string = self.source
        else:
            raise ValueError(
                "unsupported source code type: %s" % type(self.source)
            )
        command = (
            self.command[0] if isinstance(self.command, list) else self.command
        )
        script["source"] = (
            source_code_string if command.lower() == "python" else self.source
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
