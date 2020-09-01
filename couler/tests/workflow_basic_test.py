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
            [OrderedDict({"name": "flip-coin-35", "template": "flip-coin"})],
            [OrderedDict({"name": "heads-36", "template": "heads"})],
            [OrderedDict({"name": "tails-37", "template": "tails"})],
            [OrderedDict({"name": "flip-coin-38", "template": "flip-coin"})],
        ]

        self.assertEqual(steps, hope_steps)

    def test_when_order_two(self):
        couler.steps = OrderedDict()
        couler.update_steps = True
        couler.when(couler.equal(flip_coin(), "heads"), lambda: heads())
        couler.when(couler.equal(flip_coin(), "tails"), lambda: tails())

        steps = couler.workflow.get_steps_dict()
        hope_steps = [
            [OrderedDict({"name": "flip-coin-53", "template": "flip-coin"})],
            [
                OrderedDict(
                    {
                        "name": "heads-53",
                        "template": "heads",
                        "when": "{{steps.flip-coin-53.outputs.result}} == heads",  # noqa: E501
                    }
                )
            ],
            [OrderedDict({"name": "flip-coin-54", "template": "flip-coin"})],
            [
                OrderedDict(
                    {
                        "name": "tails-54",
                        "template": "tails",
                        "when": "{{steps.flip-coin-54.outputs.result}} == tails",  # noqa: E501
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
                    [("name", "flip-coin-102"), ("template", "flip-coin")]
                )
            ],
            [
                OrderedDict(
                    [
                        ("name", "heads-103"),
                        ("template", "heads"),
                        (
                            "when",
                            "{{steps.flip-coin-102.outputs.result}} == heads",
                        ),
                    ]
                ),
                OrderedDict(
                    [
                        ("name", "tails-106"),
                        ("template", "tails"),
                        (
                            "when",
                            "{{steps.flip-coin-102.outputs.result}} == tails",
                        ),
                    ]
                ),
            ],
            [
                OrderedDict(
                    [("name", "flip-coin-105"), ("template", "flip-coin")]
                )
            ],
            [
                OrderedDict(
                    [
                        ("name", "heads-107"),
                        ("template", "heads"),
                        (
                            "when",
                            "{{steps.flip-coin-105.outputs.result}} == heads",
                        ),
                    ]
                ),
                OrderedDict(
                    [
                        ("name", "tails-108"),
                        ("template", "tails"),
                        (
                            "when",
                            "{{steps.flip-coin-105.outputs.result}} == tails",
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
                    [("name", "flip-coin-177"), ("template", "flip-coin")]
                )
            ],
            [
                OrderedDict(
                    [
                        ("name", "output-message-179"),
                        ("template", "output-message"),
                        (
                            "when",
                            "{{steps.flip-coin-177.outputs.result}} > 0.2",
                        ),
                        (
                            "arguments",
                            {
                                "parameters": [
                                    {
                                        "name": "para-output-message-0",
                                        "value": '"{{steps.flip-coin-177.outputs.result}}"',  # noqa: E501
                                    }
                                ]
                            },
                        ),
                    ]
                )
            ],
        ]
        self.assertEqual(steps, expected)

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
