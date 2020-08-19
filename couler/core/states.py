from collections import OrderedDict

from couler.core import pyfunc
from couler.core.templates import Workflow

_sub_steps = None
# Argo DAG task
_update_steps_lock = True
_run_concurrent_lock = False
_concurrent_func_line = -1
# Identify concurrent functions have the same name
_concurrent_func_id = 0
# We need to fetch the name before triggering atexit, as the atexit handlers
# cannot get the original Python filename.
workflow_filename = pyfunc.workflow_filename()
workflow = Workflow(workflow_filename=workflow_filename)
# '_when_prefix' represents 'when' prefix in Argo YAML. For example,
# https://github.com/argoproj/argo/blob/master/examples/README.md#conditionals
_when_prefix = None
# '_condition_id' records the line number where the 'couler.when()' is invoked.
_condition_id = None
# '_while_steps' records the step of recursive logic
_while_steps: OrderedDict = OrderedDict()
# '_while_lock' indicts the recursive call start
_while_lock = False
# dependency edges
_upstream_dag_task = None
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


def get_step_output(step_name):
    # Return the output as a list by default
    return _steps_outputs.get(step_name, None)


def get_secret(name: str):
    """Get secret by name."""
    return _secrets.get(name, None)


def _cleanup():
    """Cleanup the cached fields, just used for unit test.
    """
    global _secrets, _update_steps_lock, _dag_caller_line, _upstream_dag_task, workflow, _steps_outputs  # noqa: E501
    _secrets = {}
    _update_steps_lock = True
    _dag_caller_line = None
    _upstream_dag_task = None
    _steps_outputs = OrderedDict()
    workflow.cleanup()
