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


def map(function, *arguments):
    """
    map operation of Couler
    """

    # Enforce the function to run and lock to add into step
    # Checks the correct syntax
    if callable(function):
        states._update_steps_lock = False

        para = []
        x = 0

        while x < len(arguments):
            para.append(arguments[x][0])
            x += 1

        inner = function(*para)

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

    # the following part of the code
    # Adds values to parameters (with items) while it goes
    # through the *arguments-variable with two loops.
    # inner loop:
    # arguments[ind_of_func_param][0], arguments[ind_of_func_param][0]...
    # Outer loop:
    # arguments[0][ind_of_func_call], arguments[0][ind_of_func_call]...
    # With two lists in *arguments
    # result would be:
    #  1. pair of items for the function:
    # arguments[0][0], arguments[1][0]
    # 2. pair of items for the function:
    #  arguments[0][1], arguments[1][1]
    # and so on...
    with_items = []
    ind_of_func_call = 0
    # the number of calls to be made to function
    while ind_of_func_call < len(arguments[0]):
        ind_of_func_param = 0
        item = {}
        # the number of parameters function takes.
        while ind_of_func_param < len(arguments):

            # checks if arguments[ind_of_func_param] is a list if not makes it
            if not isinstance(arguments[ind_of_func_param], list):
                arguments[ind_of_func_param] = [arguments[ind_of_func_param]]

            # items are created for the with items part in .yaml
            para_name = input_parameters[ind_of_func_param]["name"]
            item[para_name] = arguments[ind_of_func_param][ind_of_func_call]

            ind_of_func_param += 1
        with_items.append(item)
        ind_of_func_call += 1

    # all the created items are added to the step and
    # then the step is added to  .yaml
    inner_step.with_items = with_items
    states.workflow.add_step(inner_dict["id"], inner_step)

    return inner_step
