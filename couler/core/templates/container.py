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
from couler.core.templates.artifact import TypedArtifact
from couler.core.templates.output import OutputArtifact, OutputJob
from couler.core.templates.secret import Secret
from couler.core.templates.template import Template


class Container(Template):
    def __init__(
        self,
        name,
        image,
        command,
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
        Template.__init__(
            self,
            name=name,
            output=utils.make_list_if_not(output),
            input=utils.make_list_if_not(input),
            timeout=timeout,
            retry=retry,
            pool=pool,
            enable_ulogfs=enable_ulogfs,
            daemon=daemon,
            cache=cache,
        )
        self.image = image
        self.command = utils.make_list_if_not(command)
        self.args = args
        self.env = env
        self.secret = secret
        self.resources = resources
        self.image_pull_policy = image_pull_policy
        self.volume_mounts = volume_mounts
        self.working_dir = working_dir
        self.node_selector = node_selector
        self.volumes = volumes

    def get_volume_mounts(self):
        return self.volume_mounts

    def to_dict(self):
        template = Template.to_dict(self)
        # Inputs
        parameters = []
        if self.args is not None:
            i = 0
            for arg in self.args:
                if not isinstance(self.args[i], OutputArtifact):
                    if isinstance(arg, OutputJob):
                        for _ in range(3):
                            parameters.append(
                                {
                                    "name": utils.input_parameter_name(
                                        self.name, i
                                    )
                                }
                            )
                            i += 1
                    else:
                        para_name = utils.input_parameter_name(self.name, i)
                        parameters.append({"name": para_name})
                        i += 1

        # Input
        # Case 1: add the input parameter
        if len(parameters) > 0:
            template["inputs"] = OrderedDict()
            template["inputs"]["parameters"] = parameters

        # Case 2: add the input artifact
        if self.input is not None:
            _input_list = []
            for o in self.input:
                if isinstance(o, TypedArtifact):
                    _input_list.append(o.to_yaml())
                if isinstance(o, OutputArtifact):
                    name = o.artifact["name"]
                    if not any(name == x["name"] for x in _input_list):
                        _input_list.append(o.artifact)

            if len(_input_list) > 0:
                if "inputs" not in template:
                    template["inputs"] = OrderedDict()

                template["inputs"]["artifacts"] = _input_list

        # Node selector
        if self.node_selector is not None:
            # TODO: Support inferring node selector values from Argo parameters
            template["nodeSelector"] = self.node_selector

        # Container
        if (
            not utils.gpu_requested(self.resources)
            and states._overwrite_nvidia_gpu_envs
        ):
            if self.env is None:
                self.env = {}
            self.env.update(OVERWRITE_GPU_ENVS)
        template["container"] = self.container_dict()

        # Output
        if self.output is not None:
            _output_list = []
            for o in self.output:
                _output_list.append(o.to_yaml())

            if isinstance(o, TypedArtifact):
                # Require only one kind of output type
                template["outputs"] = {"artifacts": _output_list}
            else:
                template["outputs"] = {"parameters": _output_list}

        return template

    def container_dict(self):
        # Container part
        container = OrderedDict({"image": self.image, "command": self.command})
        if utils.non_empty(self.args):
            container["args"] = self._convert_args_to_input_parameters(
                self.args
            )
        if utils.non_empty(self.env):
            container["env"] = utils.convert_dict_to_env_list(self.env)
        if self.secret is not None:
            if not isinstance(self.secret, Secret):
                raise ValueError(
                    "Parameter secret should be an instance of Secret"
                )
            if self.env is None:
                container["env"] = self.secret.to_env_list()
            else:
                container["env"].extend(self.secret.to_env_list())
        if self.resources is not None:
            container["resources"] = {
                "requests": self.resources,
                # To fix the mojibake issue when dump yaml for one object
                "limits": copy.deepcopy(self.resources),
            }
        if self.image_pull_policy is not None:
            container["imagePullPolicy"] = utils.config_image_pull_policy(
                self.image_pull_policy
            )
        if self.volume_mounts is not None:
            container["volumeMounts"] = [
                vm.to_dict() for vm in self.volume_mounts
            ]
        if self.working_dir is not None:
            container["workingDir"] = self.working_dir
        return container

    def _convert_args_to_input_parameters(self, args):
        parameters = []
        if args is not None:
            for i in range(len(args)):
                o = args[i]
                if not isinstance(o, OutputArtifact):
                    para_name = utils.input_parameter_name(self.name, i)
                    param_full_name = '"{{inputs.parameters.%s}}"' % para_name
                    if param_full_name not in parameters:
                        parameters.append(param_full_name)

        return parameters
