import types

import couler.core.pyfunc as pyfunc
from couler.core import states
from couler.core.templates import OutputArtifact, OutputJob, OutputParameter


def dag(dependency_graph):
    """
    Generate a DAG of Argo YAML
    Note: couler.set_dependencies() is more preferable.
    https://github.com/argoproj/argo/blob/master/examples/dag-coinflip.yaml
    """
    if not isinstance(dependency_graph, list):
        raise SyntaxError("require input as list")

    states.workflow.enable_dag_mode()

    _, call_line = pyfunc.invocation_location()

    states._dag_caller_line = call_line

    for edges in dependency_graph:
        states._upstream_dag_task = None
        if isinstance(edges, list):
            for node in edges:
                if isinstance(node, types.FunctionType):
                    node()
                else:
                    raise TypeError("require loop over a function to run")


def set_dependencies(step_function, dependencies):
    """
    :param step_function: step to run
    :param dependencies: the dependencies step_name to run
    :return:
    """

    if dependencies is not None and not isinstance(dependencies, list):
        raise SyntaxError("require input as list")

    if not isinstance(step_function, types.FunctionType):
        raise SyntaxError("require step_function to a function")

    states.workflow.enable_dag_mode()

    states._upstream_dag_task = dependencies

    states._outputs_tmp = []
    if dependencies is not None:
        for step in dependencies:
            output = states.get_step_output(step)

            for o in output:
                if isinstance(o, (OutputArtifact, OutputParameter, OutputJob)):
                    states._outputs_tmp.append(o)

    ret = step_function()
    states._outputs_tmp = None
    return ret
