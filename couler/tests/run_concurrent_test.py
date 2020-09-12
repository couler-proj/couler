import os
import pyaml
import yaml
import couler.argo as couler
from couler.tests.argo_yaml_test import ArgoYamlTest




couler.config_workflow(name="pytest")


def whalesay(hello_param):
    return couler.run_container(
        image="docker/whalesay", command=["cowsay"], args=hello_param
    )


def heads():
    return couler.run_container(
        image="docker/whalesay", command='echo "it was heads"'
    )


def tails():
    return couler.run_container(
        image="docker/whalesay", command='echo "it was tails"'
    )


class ConcurrentTest(ArgoYamlTest):
    def verify_concurrent_step(self, yaml_file_name):
        _test_data_dir = "test_data"
        test_data_dir = os.path.join(os.path.dirname(__file__), _test_data_dir)
        with open(os.path.join(test_data_dir, yaml_file_name), "r") as f:
            expected = yaml.safe_load(f)
        output = yaml.safe_load(
            pyaml.dump(couler.workflow_yaml(), string_val_style="plain")
        )
        # Because test environment between local and CI is different,
        # we can not compare the YAML directly.
        steps = output["spec"]["templates"][0]["steps"][0]
        expected_steps = expected["spec"]["templates"][0]["steps"][0]

        self.assertEqual(len(steps), len(expected_steps))
        for index in range(len(steps)):
            _step = steps[index]
            _expected_step = expected_steps[index]
            self.assertEqual(_step["template"], _expected_step["template"])

    def test_run_concurrent(self):
        couler.concurrent(
            [lambda: whalesay("hello1"), lambda: heads(), lambda: tails()]
        )
        self.verify_concurrent_step("run_concurrent_golden.yaml")

    def test_run_concurrent_same_name(self):
        couler.concurrent(
            [
                lambda: whalesay("hello1"),
                lambda: whalesay("hello1"),
                lambda: tails(),
            ]
        )
        self.verify_concurrent_step("run_concurrent_golden_2.yaml")

    def test_concurrent_with_output(self):
        def job_one():
            output_place = couler.create_parameter_artifact(
                path="/tmp/job_one.txt"
            )
            return couler.run_container(
                image="python:3.6",
                args="echo -n step one > %s" % output_place.path,
                output=output_place,
            )

        def job_two():
            output_place = couler.create_parameter_artifact(
                path="/tmp/job_two.txt"
            )
            return couler.run_container(
                image="python:3.6",
                args="echo -n step two > %s" % output_place.path,
                output=output_place,
            )

        def summary(messages):
            couler.run_container(
                image="docker/whalesay", command="cowsay", args=messages
            )

        rets = couler.concurrent([lambda: job_one(), lambda: job_two()])
        messages = [rets[0][0], rets[1][0]]
        summary(messages)
        self.verify_concurrent_step("run_concurrent_golden_3.yaml")

    def test_run_concurrent_recursive(self):
        def workflow_one():
            whalesay("workflow one")
            whalesay("t1")
            whalesay("t2")

        def workflow_two():
            whalesay("workflow two")

        whalesay("workflow start")
        couler.concurrent(
            [lambda: workflow_one(), lambda: workflow_two()], subtasks=True
        )
        whalesay("workflow finish")
        self.check_argo_yaml("run_concurrent_subtasks_golden.yaml")
