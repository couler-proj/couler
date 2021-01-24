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


from couler.core import states, utils
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

    _, call_line = utils.invocation_location()

    states._dag_caller_line = call_line

    for edges in dependency_graph:
        states._upstream_dag_task = None
        if isinstance(edges, list):
            for node in edges:
                if callable(node):
                    node()
                else:
                    raise TypeError("require loop over a function to run")


def set_dependencies(step_function, dependencies=None):
    """
    :param step_function: step to run
    :param dependencies: the list of dependencies of this step. This can be in
        either of the following forms:
        1. a list of step names;
        2. a string representing the enhanced depends logic that specifies
        dependencies based on their statuses. See the link below for the
        supported syntax:
        https://github.com/argoproj/argo/blob/master/docs/enhanced-depends-logic.md
    :return:
    """

    if dependencies is not None:
        if isinstance(dependencies, list):
            # A list of dependencies
            states._upstream_dag_task = dependencies
            states._upstream_dag_depends_logic = None
        elif isinstance(dependencies, str):
            # Dependencies using enhanced depends logic
            states._upstream_dag_depends_logic = dependencies
            states._upstream_dag_task = None
        else:
            raise SyntaxError("dependencies must be a list or a string")
    else:
        states._upstream_dag_depends_logic = None
        states._upstream_dag_task = None
    if not callable(step_function):
        raise SyntaxError("require step_function to a function")

    states.workflow.enable_dag_mode()

    states._outputs_tmp = []
    if dependencies is not None and isinstance(dependencies, list):
        for step in dependencies:
            output = states.get_step_output(step)

            for o in output:
                if isinstance(o, (OutputArtifact, OutputParameter, OutputJob)):
                    states._outputs_tmp.append(o)

    ret = step_function()
    states._outputs_tmp = None
    return ret
