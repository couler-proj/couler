import types

from couler.core import pyfunc, states
from couler.core.templates import Step


def when(condition, function):
    """Generates an Argo conditional step.
    For example, the coinflip example in
    https://github.com/argoproj/argo/blob/master/examples/coinflip.yaml.
    """
    pre = condition["pre"]
    post = condition["post"]
    if pre is None or post is None:
        raise SyntaxError("Output of function can not be null")

    condition_suffix = condition["condition"]

    pre_dict = pyfunc.extract_step_return(pre)
    post_dict = pyfunc.extract_step_return(post)

    if "name" in pre_dict:
        left_function_id = pre_dict["id"]
        if states.workflow.get_step(left_function_id) is None:
            states.workflow.add_step(
                name=left_function_id,
                step=Step(name=left_function_id, template=pre_dict["name"]),
            )
    else:
        # TODO: fixed if left branch is a variable rather than function
        pre_dict["value"]

    post_value = post_dict["value"]

    states._when_prefix = "{{steps.%s.%s}} %s %s" % (
        pre_dict["id"],
        pre_dict["output"],
        condition_suffix,
        post_value,
    )
    states._condition_id = "%s.%s" % (pre_dict["id"], pre_dict["output"])

    # Enforce the function to run and lock to add into step
    if isinstance(function, types.FunctionType):
        function()
    else:
        raise TypeError("condition to run would be a function")

    states._when_prefix = None
    states._condition_id = None
