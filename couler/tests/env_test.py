import copy
import unittest

import couler.argo as couler


class EnvUnitTest(unittest.TestCase):
    def setUp(self):
        couler._cleanup()
        self.envs = {"str_env": "abc", "bool_env": False, "num_env": 1234}

    def run_a_container(self):
        couler.run_container(
            image="python:3.6",
            env=copy.deepcopy(self.envs),
            command=["bash", "-c", """echo ${MESSAGE}"""],
        )

    def run_a_script(self):
        couler.run_script(
            image="python:3.6", env=copy.deepcopy(self.envs), source=self.setUp
        )

    def run_a_gpu_container(self):
        couler.run_container(
            image="python:3.6",
            env=copy.deepcopy(self.envs),
            resources={"cpu": 1, "memory": 1024, "gpu": 1},
            command=["bash", "-c", """echo ${MESSAGE}"""],
        )

    def run_a_gpu_script(self):
        couler.run_script(
            image="python:3.6",
            env=copy.deepcopy(self.envs),
            resources={"cpu": 1, "memory": 1024, "gpu": 1},
            source=self.setUp,
        )

    def test_run_container_env(self):
        self.run_a_container()
        workflow = couler.workflow_yaml()
        checked = False
        for template in workflow["spec"]["templates"]:
            if template["name"] == "run-a-container":
                checked = True
                container = template["container"]
                self.assertEqual(len(container), 3)
                self.assertEqual(container["image"], "python:3.6")
                self.assertEqual(
                    container["command"], ["bash", "-c", "echo ${MESSAGE}"]
                )
                self.assertEqual(len(container["env"]), len(self.envs))
                for env in container["env"]:
                    if env["name"] == "str_env":
                        self.assertEqual(env["value"], self.envs["str_env"])
                    elif env["name"] == "bool_env":
                        self.assertEqual(
                            env["value"], "'%s'" % self.envs["bool_env"]
                        )
                    elif env["name"] == "num_env":
                        self.assertEqual(
                            env["value"], "%s" % self.envs["num_env"]
                        )
        self.assertTrue(checked)

    def test_run_script_env(self):
        self.run_a_script()
        workflow = couler.workflow_yaml()
        checked = False
        for template in workflow["spec"]["templates"]:
            if template["name"] == "run-a-script":
                checked = True
                script = template["script"]
                self.assertEqual(len(script), 4)
                self.assertEqual(script["image"], "python:3.6")
                self.assertEqual(script["command"], ["python"])
                self.assertEqual(len(script["env"]), len(self.envs))
                for env in script["env"]:
                    if env["name"] == "str_env":
                        self.assertEqual(env["value"], self.envs["str_env"])
                    elif env["name"] == "bool_env":
                        self.assertEqual(
                            env["value"], "'%s'" % self.envs["bool_env"]
                        )
                    elif env["name"] == "num_env":
                        self.assertEqual(
                            env["value"], "%s" % self.envs["num_env"]
                        )
        self.assertTrue(checked)

    def test_run_gpu_container_env(self):
        self.run_a_gpu_container()
        workflow = couler.workflow_yaml()
        checked = False
        for template in workflow["spec"]["templates"]:
            if template["name"] == "run-a-gpu-container":
                checked = True
                container = template["container"]
                self.assertEqual(len(container), 4)
                self.assertEqual(container["image"], "python:3.6")
                self.assertEqual(
                    container["command"], ["bash", "-c", "echo ${MESSAGE}"]
                )
                self.assertEqual(len(container["env"]), len(self.envs))
                for env in container["env"]:
                    if env["name"] not in self.envs:
                        raise AssertionError(
                            "Unrecognized env variable %s" % env["name"]
                        )
                    elif env["name"] == "str_env":
                        self.assertEqual(env["value"], self.envs["str_env"])
                    elif env["name"] == "bool_env":
                        self.assertEqual(
                            env["value"], "'%s'" % self.envs["bool_env"]
                        )
                    elif env["name"] == "num_env":
                        self.assertEqual(
                            env["value"], "%s" % self.envs["num_env"]
                        )
        self.assertTrue(checked)

    def test_run_gpu_script_env(self):
        self.run_a_gpu_script()
        workflow = couler.workflow_yaml()
        checked = False
        for template in workflow["spec"]["templates"]:
            if template["name"] == "run-a-gpu-script":
                checked = True
                script = template["script"]
                self.assertEqual(len(script), 5)
                self.assertEqual(script["image"], "python:3.6")
                self.assertEqual(script["command"], ["python"])
                self.assertEqual(len(script["env"]), len(self.envs))
                for env in script["env"]:
                    if env["name"] not in self.envs:
                        raise AssertionError(
                            "Unrecognized env variable %s" % env["name"]
                        )
                    elif env["name"] == "str_env":
                        self.assertEqual(env["value"], self.envs["str_env"])
                    elif env["name"] == "bool_env":
                        self.assertEqual(
                            env["value"], "'%s'" % self.envs["bool_env"]
                        )
                    elif env["name"] == "num_env":
                        self.assertEqual(
                            env["value"], "%s" % self.envs["num_env"]
                        )
        self.assertTrue(checked)
