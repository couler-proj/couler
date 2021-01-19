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

import couler.argo as couler
from couler.tests.argo_yaml_test import ArgoYamlTest

couler.config_workflow(name="pytest")


def random_code():
    import random

    result = random.randint(0, 1)
    print(result)


def generate_number():
    return couler.run_script(image="python:3.6", source=random_code)


def whalesay(hello_param):
    return couler.run_container(
        image="docker/whalesay", command=["cowsay"], args=hello_param
    )


def whalesay_two(hello_param1, hello_param2):
    return couler.run_container(
        image="docker/whalesay",
        command=["cowsay"],
        args=[hello_param1, hello_param2],
    )


class InputParametersTest(ArgoYamlTest):
    def test_input_basic(self):
        whalesay("hello1")
        inputs = couler.workflow.get_template("whalesay").to_dict()["inputs"]
        expected_inputs = OrderedDict(
            [("parameters", [{"name": "para-whalesay-0"}])]
        )
        self.assertEqual(inputs, expected_inputs)

    def test_input_basic_two_calls(self):
        whalesay("hello1")
        whalesay("hello2")

        self.check_argo_yaml("input_para_golden_1.yaml")

    def test_input_basic_two_paras_2(self):
        whalesay_two("hello1", "hello2")
        whalesay_two("x", "y")

        self.check_argo_yaml("input_para_golden_2.yaml")

    def test_input_steps_1(self):
        message = "test"
        whalesay(message)
        message = generate_number()
        whalesay(message)

        self.check_argo_yaml("input_para_golden_3.yaml")

    def test_input_arg_as_string(self):
        def whalesay(hello_param):
            return couler.run_container(
                image="docker/whalesay", command=["cowsay"], args=hello_param
            )

        whalesay("test")

        self.check_argo_yaml("input_para_golden_4.yaml")

    def test_input_args_as_othertypes(self):
        def whalesay(para_integer, para_boolean, para_float):
            return couler.run_container(
                image="docker/whalesay",
                command=["cowsay"],
                args=[para_integer, para_boolean, para_float],
            )

        whalesay(1, True, 1.1)

        wf = couler.workflow_yaml()
        parameters = wf["spec"]["templates"][0]["steps"][0][0]["arguments"][
            "parameters"
        ]
        self.assertEqual(int(parameters[0]["value"].strip(" " "' ")), 1)
        self.assertEqual(bool(parameters[1]["value"].strip(" " "' ")), True)
        self.assertEqual(float(parameters[2]["value"].strip(" " "' ")), 1.1)
