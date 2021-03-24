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
from couler.core.templates import Workflow

try:
    from couler.core.proto_repr import cleanup_proto_workflow
except Exception:
    # set cleanup_proto_workflow to an empty function for compatibility
    cleanup_proto_workflow = lambda: None  # noqa: E731

_sub_steps = None
# Argo DAG task
_update_steps_lock = True
_run_concurrent_lock = False
_concurrent_func_line = -1
# Identify concurrent functions have the same name
_concurrent_func_id = 0
# We need to fetch the name before triggering atexit, as the atexit handlers
# cannot get the original Python filename.
workflow_filename = utils.workflow_filename()
workflow = Workflow(workflow_filename=workflow_filename)
# '_when_prefix' represents 'when' prefix in Argo YAML. For example,
# https://github.com/argoproj/argo/blob/master/examples/README.md#conditionals
_when_prefix = None
_when_task = None
# '_condition_id' records the line number where the 'couler.when()' is invoked.
_condition_id = None
# '_while_steps' records the step of recursive logic
_while_steps: OrderedDict = OrderedDict()
# '_while_lock' indicts the recursive call start
_while_lock = False
# dependency edges
_upstream_dag_task = None
# Enhanced depends logic
_upstream_dag_depends_logic = None
# dag function caller line
_dag_caller_line = None
# start exit handler
_exit_handler_enable = False
# step output results
_steps_outputs: OrderedDict = OrderedDict()
_secrets: dict = {}
# for passing the artifact implicitly
_outputs_tmp = None
# print yaml at exit
_enable_print_yaml = True
# Whether to overwrite NVIDIA GPU environment variables
# to containers and templates
_overwrite_nvidia_gpu_envs = False


def get_step_output(step_name):
    # Return the output as a list by default
    return _steps_outputs.get(step_name, None)


def get_secret(name: str):
    """Get secret by name."""
    return _secrets.get(name, None)


def _cleanup():
    """Cleanup the cached fields, just used for unit test.
    """
    global _secrets, _update_steps_lock, _dag_caller_line, _upstream_dag_task, _upstream_dag_depends_logic, workflow, _steps_outputs  # noqa: E501
    global _exit_handler_enable, _when_prefix, _when_task, _while_steps, _concurrent_func_line  # noqa: E501
    _secrets = {}
    _update_steps_lock = True
    _dag_caller_line = None
    _upstream_dag_task = None
    _upstream_dag_depends_logic = None
    _exit_handler_enable = False
    _when_prefix = None
    _when_task = None
    _while_steps = OrderedDict()
    _concurrent_func_line = -1
    _steps_outputs = OrderedDict()
    workflow.cleanup()
    cleanup_proto_workflow()
