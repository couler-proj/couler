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


import pyaml
import yaml

from couler.core import states
from couler.core.templates import Step, output


def map(function, input_list):
    """
    map operation of Couler
    """
    # Enforce the function to run and lock to add into step
    if callable(function):
        states._update_steps_lock = False
        # TODO (terrytangyuan): Support functions with multiple arguments.
        para = input_list[0]
        inner = function(para)
        if inner is None:
            raise SyntaxError("require function return value")
        states._update_steps_lock = True
    else:
        raise TypeError("require loop over a function to run")

    inner_dict = output.extract_step_return(inner)
    template_name = inner_dict["name"]
    inner_step = Step(name=inner_dict["id"], template=template_name)

    parameters = []
    items_param_name = "%s-para-name" % template_name
    items_param_dict = {"name": items_param_name}
    function_template = states.workflow.get_template(template_name)
    function_template_dict = function_template.to_dict()

    if "resource" in function_template_dict:
        # Update the template with the new dynamic `metadata.name`.
        manifest_dict = yaml.safe_load(
            function_template_dict["resource"]["manifest"]
        )
        manifest_dict["metadata"]["name"] = (
            "'{{inputs.parameters.%s}}'" % items_param_name
        )
        function_template = states.workflow.get_template(template_name)
        function_template.manifest = pyaml.dump(manifest_dict)
        # Append this items parameter to input parameters in the template
        function_template.args.append(items_param_dict)
        states.workflow.add_template(function_template)
        input_parameters = [items_param_dict]
    else:
        input_parameters = function_template_dict["inputs"]["parameters"]

    for para_name in input_parameters:
        parameters.append(
            {
                "name": para_name["name"],
                "value": '"{{item.%s}}"' % para_name["name"],
            }
        )

    inner_step.arguments = {"parameters": parameters}

    with_items = []
    for para_values in input_list:
        item = {}
        if not isinstance(para_values, list):
            para_values = [para_values]

        for j in range(len(input_parameters)):
            para_name = input_parameters[j]["name"]
            item[para_name] = para_values[j]

        with_items.append(item)

    inner_step.with_items = with_items
    states.workflow.add_step(inner_dict["id"], inner_step)

    return inner_step
