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


from couler.core import states
from couler.core.constants import WFStatus


def set_exit_handler(status, exit_handler):
    """
    Configure the workflow handler
    Status would be: Succeeded, Failed, or Error.
    Each status invokes one exit_handler function.
    https://github.com/argoproj/argo/blob/master/examples/exit-handlers.yaml
    """
    if not callable(exit_handler):
        raise SyntaxError("require exit handler is a function")

    if not isinstance(status, WFStatus):  # noqa: F405
        raise SyntaxError(
            "require input status to be Succeeded, Failed or Error"
        )

    workflow_status = "{{workflow.status}} == %s" % status.value

    states._exit_handler_enable = True
    states._when_prefix = workflow_status

    branch = exit_handler()
    if branch is None:
        raise SyntaxError("require function return value")

    states._when_prefix = None
    states._exit_handler_enable = False
