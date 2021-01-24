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
from couler.core.templates import Step, output


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

    pre_dict = output.extract_step_return(pre)
    post_dict = output.extract_step_return(post)

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

    if states._upstream_dag_task is not None:
        step_type = "tasks"
        states._when_task = pre_dict["id"]
    else:
        step_type = "steps"
    states._when_prefix = "{{%s.%s.%s}} %s %s" % (
        step_type,
        pre_dict["id"],
        pre_dict["output"],
        condition_suffix,
        post_value,
    )
    states._condition_id = "%s.%s" % (pre_dict["id"], pre_dict["output"])

    # Enforce the function to run and lock to add into step
    if callable(function):
        function()
    else:
        raise TypeError("condition to run would be a function")

    states._when_prefix = None
    states._condition_id = None
