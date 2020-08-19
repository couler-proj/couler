from collections import OrderedDict

from couler.core import pyfunc


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
    ):
        self.name = name
        self.output = output
        self.input = input
        self.timeout = timeout
        self.retry = retry
        self.pool = pool
        self.enable_ulogfs = enable_ulogfs
        self.daemon = daemon

    def to_dict(self):
        template = OrderedDict({"name": self.name})
        if self.daemon:
            template["daemon"] = True
        if self.timeout is not None:
            template["activeDeadlineSeconds"] = self.timeout
        if self.retry is not None:
            template["retryStrategy"] = pyfunc.config_retry_strategy(
                self.retry
            )
        return template
