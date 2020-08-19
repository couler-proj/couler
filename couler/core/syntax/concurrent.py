import types
from collections import OrderedDict

from couler.core import pyfunc, states
from couler.core.step_update_utils import _update_steps
from couler.core.templates import Steps


def concurrent(function_list, subtasks=False):
    """
    Start different jobs at the same time
    subtasks: each function F of function_list contains multiple steps.
    Then, for each F, we create a sub-steps template.
    """
    if not isinstance(function_list, list):
        raise SyntaxError("require input functions as list")

    _, con_caller_line = pyfunc.invocation_location()

    states._concurrent_func_line = con_caller_line
    states._run_concurrent_lock = True

    function_rets = []
    for function in function_list:
        # In case different parallel steps use the same function name
        states._concurrent_func_id = states._concurrent_func_id + 1
        if isinstance(function, types.FunctionType):
            if subtasks is True:
                # 1. generate the sub-steps template
                # 2. for each step in F, update the sub_steps template
                # 3. append the steps into the template
                # 4. for F itself, update the main control flow step
                states._sub_steps = OrderedDict()
                tmp_concurrent_func_id = states._concurrent_func_id
                states._run_concurrent_lock = False
                ret = function()
                states._concurrent_func_id = tmp_concurrent_func_id
                func_name = "concurrent-task-%s" % states._concurrent_func_id
                template = Steps(
                    name=func_name, steps=list(states._sub_steps.values())
                )
                states.workflow.add_template(template)
                states._sub_steps = None
                # TODO: add the args for the sub task
                states._run_concurrent_lock = True
                _update_steps(
                    "concurrent_func_name",
                    con_caller_line,
                    args=None,
                    template_name=func_name,
                )
            else:
                ret = function()

            function_rets.append(ret)
        else:
            raise TypeError("require loop over a function to run")

    states._run_concurrent_lock = False
    states._concurrent_func_id = 0

    return function_rets
