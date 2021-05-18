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

import unittest
from collections import OrderedDict

import couler.argo as couler
from couler.tests.argo_yaml_test import ArgoYamlTest

_test_data_dir = "test_data"
couler.config_workflow(name="pytest")


def random_code():
    import random

    result = "heads" if random.randint(0, 1) == 0 else "tails"
    print(result)


def flip_coin():
    return couler.run_script(image="python:3.6", source=random_code)


def heads():
    return couler.run_container(
        image="python:3.6", command=["bash", "-c", 'echo "it was heads"']
    )


def tails():
    return couler.run_container(
        image="python:3.6", command=["bash", "-c", 'echo "it was tails"']
    )


class WorkflowBasicTest(ArgoYamlTest):
    def test_steps_order(self):
        flip_coin()
        heads()
        tails()
        flip_coin()

        steps = couler.workflow.get_steps_dict()
        hope_steps = [
            [OrderedDict({"name": "flip-coin-49", "template": "flip-coin"})],
            [OrderedDict({"name": "heads-50", "template": "heads"})],
            [OrderedDict({"name": "tails-51", "template": "tails"})],
            [OrderedDict({"name": "flip-coin-52", "template": "flip-coin"})],
        ]

        self.assertEqual(steps, hope_steps)

    def test_when_order_two(self):
        couler.steps = OrderedDict()
        couler.update_steps = True
        couler.when(couler.equal(flip_coin(), "heads"), lambda: heads())
        couler.when(couler.equal(flip_coin(), "tails"), lambda: tails())

        steps = couler.workflow.get_steps_dict()
        hope_steps = [
            [OrderedDict({"name": "flip-coin-67", "template": "flip-coin"})],
            [
                OrderedDict(
                    {
                        "name": "heads-67",
                        "template": "heads",
                        "when": "{{steps.flip-coin-67.outputs.result}} == heads",  # noqa: E501
                    }
                )
            ],
            [OrderedDict({"name": "flip-coin-68", "template": "flip-coin"})],
            [
                OrderedDict(
                    {
                        "name": "tails-68",
                        "template": "tails",
                        "when": "{{steps.flip-coin-68.outputs.result}} == tails",  # noqa: E501
                    }
                )
            ],
        ]

        self.assertEqual(hope_steps, steps)

    def test_when_callable(self):
        couler.steps = OrderedDict()
        couler.update_steps = True
        cls = self.create_callable_cls(lambda: heads())
        instance = cls()
        func_names = ["a", "b", "c", "self"]
        for func_name in func_names:
            if func_name == "self":
                couler.when(couler.equal(flip_coin(), "heads"), instance)
            else:
                couler.when(
                    couler.equal(flip_coin(), "heads"),
                    getattr(instance, func_name),
                )
            couler.when(couler.equal(flip_coin(), "tails"), lambda: tails())
            couler._cleanup()

    def test_when_order_three(self):
        couler.steps = OrderedDict()
        couler.update_steps = True
        output_1 = flip_coin()
        couler.when(couler.equal(output_1, "heads"), lambda: heads())

        output_2 = flip_coin()
        couler.when(couler.equal(output_1, "tails"), lambda: tails())
        couler.when(couler.equal(output_2, "heads"), lambda: heads())
        couler.when(couler.equal(output_2, "tails"), lambda: tails())

        steps = couler.workflow.get_steps_dict()
        hope_steps = [
            [
                OrderedDict(
                    [("name", "flip-coin-116"), ("template", "flip-coin")]
                )
            ],
            [
                OrderedDict(
                    [
                        ("name", "heads-117"),
                        ("template", "heads"),
                        (
                            "when",
                            "{{steps.flip-coin-116.outputs.result}} == heads",
                        ),
                    ]
                ),
                OrderedDict(
                    [
                        ("name", "tails-120"),
                        ("template", "tails"),
                        (
                            "when",
                            "{{steps.flip-coin-116.outputs.result}} == tails",
                        ),
                    ]
                ),
            ],
            [
                OrderedDict(
                    [("name", "flip-coin-119"), ("template", "flip-coin")]
                )
            ],
            [
                OrderedDict(
                    [
                        ("name", "heads-121"),
                        ("template", "heads"),
                        (
                            "when",
                            "{{steps.flip-coin-119.outputs.result}} == heads",
                        ),
                    ]
                ),
                OrderedDict(
                    [
                        ("name", "tails-122"),
                        ("template", "tails"),
                        (
                            "when",
                            "{{steps.flip-coin-119.outputs.result}} == tails",
                        ),
                    ]
                ),
            ],
        ]
        self.assertEqual(hope_steps, steps)

    def test_when_with_parameter(self):
        def output_message(message):
            return couler.run_container(
                image="docker/whalesay:latest",
                command=["cowsay"],
                args=[message],
            )

        number = flip_coin()
        couler.when(
            couler.bigger(number, "0.2"), lambda: output_message(number)
        )

        steps = couler.workflow.get_steps_dict()
        expected = [
            [
                OrderedDict(
                    [("name", "flip-coin-191"), ("template", "flip-coin")]
                )
            ],
            [
                OrderedDict(
                    [
                        ("name", "output-message-193"),
                        ("template", "output-message"),
                        (
                            "when",
                            "{{steps.flip-coin-191.outputs.result}} > 0.2",
                        ),
                        (
                            "arguments",
                            {
                                "parameters": [
                                    {
                                        "name": "para-output-message-0",
                                        "value": '"{{steps.flip-coin-191.outputs.result}}"',  # noqa: E501
                                    }
                                ]
                            },
                        ),
                    ]
                )
            ],
        ]
        self.assertEqual(steps, expected)

    def test_workflow_service_account(self):
        self.assertIsNone(couler.workflow.service_account)
        flip_coin()
        self.assertNotIn("serviceAccountName", couler.workflow_yaml()["spec"])

        couler.config_workflow(service_account="test-serviceaccount")
        self.assertEqual(
            couler.workflow.service_account, "test-serviceaccount"
        )
        self.assertEqual(
            couler.workflow_yaml()["spec"]["serviceAccountName"],
            "test-serviceaccount",
        )

        couler._cleanup()
        self.assertIsNone(couler.workflow.service_account)

    def test_workflow_security_context(self):
        """
        The securityContext configuration mostly taken from
        https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
        """
        self.assertIsNone(couler.workflow.security_context)
        flip_coin()
        self.assertNotIn("securityContext", couler.workflow_yaml()["spec"])

        couler.states.workflow.set_security_context(
            security_context={
                "fsGroup": 2000,
                "runAsNonRoot": True,
                "runAsUser": 1000,
                "fsGroupChangePolicy": "OnRootMismatch",
                "runAsGroup": 3000,
                "supplementalGroups": [1000, 4000, 4500],
                "seLinuxOptions": {"level": "s0:c123,c456"},
                "seccompProfile": {
                    "localhostProfile": "my-profiles/profile-allow.json",
                    "type": "Localhost",
                },
                "sysctls": [
                    {"name": "kernel.shm_rmid_forced", "value": "0"},
                    {"name": "net.core.somaxconn", "value": "1024"},
                ],
            }
        )

        self.assertTrue(couler.workflow.security_context is not None)

        actual_wf = couler.workflow_yaml()
        self.assertIn("securityContext", actual_wf["spec"])
        actual_security_context = actual_wf["spec"]["securityContext"]

        self.assertEqual(actual_security_context["fsGroup"], 2000)
        self.assertEqual(actual_security_context["runAsNonRoot"], True)
        self.assertEqual(actual_security_context["runAsUser"], 1000)
        self.assertEqual(
            actual_security_context["fsGroupChangePolicy"], "OnRootMismatch"
        )
        self.assertEqual(actual_security_context["runAsGroup"], 3000)
        self.assertEqual(
            actual_security_context["supplementalGroups"], [1000, 4000, 4500]
        )
        self.assertEqual(
            actual_security_context["seLinuxOptions"]["level"], "s0:c123,c456"
        )
        self.assertEqual(
            actual_security_context["seccompProfile"]["localhostProfile"],
            "my-profiles/profile-allow.json",
        )
        self.assertEqual(
            actual_security_context["seccompProfile"]["type"], "Localhost"
        )
        self.assertEqual(
            actual_security_context["sysctls"][0]["name"],
            "kernel.shm_rmid_forced",
        )
        self.assertEqual(actual_security_context["sysctls"][0]["value"], "0")
        self.assertEqual(
            actual_security_context["sysctls"][1]["name"], "net.core.somaxconn"
        )
        self.assertEqual(
            actual_security_context["sysctls"][1]["value"], "1024"
        )

        couler._cleanup()
        self.assertFalse(couler.workflow.security_context is not None)

    def test_workflow_config(self):
        flip_coin()
        tails()
        couler.config_workflow(
            name="test-workflow", user_id="88888888", time_to_clean=100
        )
        wf = couler.workflow_yaml()
        expected_meta = {
            "name": "test-workflow",
            # "labels": {"couler_job_user": "88888888"},
        }
        self.assertEqual(wf["metadata"], expected_meta)

    def test_set_workflow_exit_handler(self):
        couler._cleanup()

        flip_coin()
        couler.set_exit_handler(couler.WFStatus.Succeeded, heads)
        couler.set_exit_handler(couler.WFStatus.Failed, tails)
        self.check_argo_yaml("workflow_basic_golden.yaml")
        couler._cleanup()

    def test_exit_callable(self):
        cls = self.create_callable_cls(lambda: heads())
        instance = cls()
        func_names = ["a", "b", "c", "self"]
        for func_name in func_names:
            flip_coin()
            if func_name == "self":
                couler.set_exit_handler(couler.WFStatus.Succeeded, instance)
            else:
                couler.set_exit_handler(
                    couler.WFStatus.Succeeded, getattr(instance, func_name)
                )
            couler.set_exit_handler(couler.WFStatus.Failed, tails)
            self.check_argo_yaml("workflow_basic_golden.yaml")
            couler._cleanup()

    def test_string_sourcecode(self):
        code = """print("hello world")"""
        couler.run_script(image="python:3.6", source=code)
        ret = couler.workflow_yaml()
        self.assertEqual(code, ret["spec"]["templates"][1]["script"]["source"])


if __name__ == "__main__":
    unittest.main()
