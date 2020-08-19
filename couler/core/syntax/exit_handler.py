import types

from couler.core import states
from couler.core.constants import WFStatus


def set_exit_handler(status, exit_handler):
    """
    Configure the workflow handler
    Status would be: Succeeded, Failed, or Error.
    Each status invokes one exi_handler function.
    https://github.com/argoproj/argo/blob/master/examples/exit-handlers.yaml
    """
    if not isinstance(exit_handler, types.FunctionType):
        raise SyntaxError("require exit handler is a function")

    if not isinstance(status, WFStatus):  # noqa: F405
        raise SyntaxError(
            "require input status to be Succeeded, Failed or Error"
        )

    workflow_status = "{{workflow.status}} == %s" % status.value

    states._exit_handler_enable = True
    states._when_prefix = workflow_status

    if isinstance(exit_handler, types.FunctionType):
        branch = exit_handler()
        if branch is None:
            raise SyntaxError("require function return value")
    else:
        raise TypeError("condition to run would be a function")

    states._when_prefix = None
    states._exit_handler_enable = False
