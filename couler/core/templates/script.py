import copy
from collections import OrderedDict

from couler.core import pyfunc
from couler.core.constants import OVERWRITE_GPU_ENVS
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
        if not pyfunc.gpu_requested(self.resources):
            if self.env is None:
                self.env = {}
            self.env.update(OVERWRITE_GPU_ENVS)
        template["script"] = self.script_dict()
        return template

    def script_dict(self):
        script = OrderedDict({"image": self.image, "command": [self.command]})
        script["source"] = (
            pyfunc.body(self.source)
            if self.command.lower() == "python"
            else self.source
        )
        if pyfunc.non_empty(self.env):
            script["env"] = pyfunc.convert_dict_to_env_list(self.env)

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
            script["imagePullPolicy"] = pyfunc.config_image_pull_policy(
                self.image_pull_policy
            )
        return script
