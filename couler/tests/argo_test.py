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

import yaml

import couler.argo as couler
from couler.core import states
from couler.core.templates.volume import Volume, VolumeMount
from couler.core.templates.volume_claim import VolumeClaimTemplate


class ArgoBaseTestCase(unittest.TestCase):
    def setUp(self):
        self.state_keys = dir(states)
        self.tc_dump = {}
        for key in self.state_keys:
            if key.startswith("__"):
                continue
            if key.startswith("_"):
                value = getattr(states, key)
                if callable(value):
                    continue
                self.tc_dump[key] = value
        couler._cleanup()

    def tearDown(self):
        couler._cleanup()
        for key in self.state_keys:
            if key.startswith("__"):
                continue
            if key.startswith("_"):
                value = getattr(states, key)
                if callable(value):
                    continue
                self.assertEqual(
                    value, self.tc_dump[key], msg="state not cleanup:%s" % key
                )


class ArgoTest(ArgoBaseTestCase):
    def setUp(self):
        couler._cleanup()
        super().setUp()

    def test_run_none_source(self):
        with self.assertRaises(ValueError):
            couler.run_script(image="image1", command="python")

    def test_run_bash_script(self):
        self.assertEqual(len(couler.workflow.templates), 0)
        couler.run_script(image="image1", command="bash", source="ls")
        self.assertEqual(len(couler.workflow.templates), 1)
        template = couler.workflow.get_template(
            "test-run-bash-script"
        ).to_dict()
        self.assertEqual("test-run-bash-script", template.get("name"))
        self._verify_script_body(
            template["script"],
            image="image1",
            command=["bash"],
            source="ls",
            env=None,
        )

    def test_run_python_script(self):
        self.assertEqual(len(couler.workflow.templates), 0)
        couler.run_script("image1", command="python", source=self.setUp)
        self.assertEqual(len(couler.workflow.templates), 1)
        template = couler.workflow.get_template(
            "test-run-python-script"
        ).to_dict()
        self.assertEqual("test-run-python-script", template["name"])
        self._verify_script_body(
            template["script"],
            image="image1",
            command=["python"],
            source="\ncouler._cleanup()\nsuper().setUp()\n",
            env=None,
        )

    def test_run_default_script(self):
        # Command is not specified, should use python
        self.assertEqual(len(couler.workflow.templates), 0)
        couler.run_script("image1", source=self.setUp)
        self.assertEqual(len(couler.workflow.templates), 1)
        template = couler.workflow.get_template(
            "test-run-default-script"
        ).to_dict()
        self.assertEqual("test-run-default-script", template["name"])
        self._verify_script_body(
            template["script"],
            image="image1",
            command=["python"],
            source="\ncouler._cleanup()\nsuper().setUp()\n",
            env=None,
        )

    def test_run_container_with_volume(self):
        volume = Volume("workdir", "my-existing-volume")
        volume_mount = VolumeMount("workdir", "/mnt/vol")
        couler.add_volume(volume)
        couler.run_container(
            image="docker/whalesay:latest",
            args=["echo -n hello world"],
            command=["bash", "-c"],
            step_name="A",
            volume_mounts=[volume_mount],
            working_dir="/mnt/src",
        )

        wf = couler.workflow_yaml()
        self.assertEqual(wf["spec"]["volumes"][0], volume.to_dict())
        self.assertEqual(
            wf["spec"]["templates"][1]["container"]["volumeMounts"][0],
            volume_mount.to_dict(),
        )
        self.assertEqual(
            wf["spec"]["templates"][1]["container"]["workingDir"], "/mnt/src"
        )
        couler._cleanup()

    def test_run_container_with_node_selector(self):
        couler.run_container(
            image="docker/whalesay:latest",
            args=["echo -n hello world"],
            command=["bash", "-c"],
            step_name="A",
            node_selector={"beta.kubernetes.io/arch": "amd64"},
        )

        wf = couler.workflow_yaml()
        self.assertEqual(
            wf["spec"]["templates"][1]["nodeSelector"],
            {"beta.kubernetes.io/arch": "amd64"},
        )
        couler._cleanup()

    def test_run_container_with_workflow_volume(self):
        pvc = VolumeClaimTemplate("workdir")
        volume_mount = VolumeMount("workdir", "/mnt/vol")
        couler.create_workflow_volume(pvc)
        couler.run_container(
            image="docker/whalesay:latest",
            args=["echo -n hello world"],
            command=["bash", "-c"],
            step_name="A",
            volume_mounts=[volume_mount],
        )
        volume_mount = VolumeMount("workdir", "/mnt/vol")
        couler.run_container(
            image="docker/whalesay:latest",
            args=["echo -n hello world"],
            command=["bash", "-c"],
            step_name="A",
            volume_mounts=[volume_mount],
        )

        wf = couler.workflow_yaml()
        self.assertEqual(len(wf["spec"]["volumeClaimTemplates"]), 1)
        self.assertEqual(wf["spec"]["volumeClaimTemplates"][0], pvc.to_dict())
        self.assertEqual(
            wf["spec"]["templates"][1]["container"]["volumeMounts"][0],
            volume_mount.to_dict(),
        )
        couler._cleanup()

    def test_artifact_passing_script(self):
        def producer():
            output_artifact = couler.create_local_artifact(path="/mnt/t1.txt")
            outputs = couler.run_script(
                image="docker/whalesay:latest",
                args=["echo -n hello world > %s" % output_artifact.path],
                command=["bash", "-c"],
                output=output_artifact,
                source="sadfa\nasdf",
                step_name="producer",
            )

            return outputs

        def consumer(inputs):
            # read the content from an OSS bucket
            couler.run_script(
                image="docker/whalesay:latest",
                args=inputs,
                command=[("cat %s" % inputs[0].path)],
                source="sadfa\nasdf",
            )

        outputs = couler.set_dependencies(
            lambda: producer(), dependencies=None
        )
        couler.set_dependencies(
            lambda: consumer(outputs), dependencies=["producer"]
        )

        wf = couler.workflow_yaml()
        dag = wf["spec"]["templates"][0]["dag"]
        self.assertEqual(len(dag["tasks"][1]["arguments"]["artifacts"]), 1)
        self.assertIsInstance(
            dag["tasks"][1]["arguments"]["artifacts"][0]["from"], str
        )
        self.assertIsInstance(
            dag["tasks"][1]["arguments"]["artifacts"][0]["name"], str
        )
        template = wf["spec"]["templates"][1]
        self.assertEqual(len(template["outputs"]["artifacts"]), 1)
        template = wf["spec"]["templates"][2]
        self.assertEqual(len(template["inputs"]["artifacts"]), 1)
        self.assertNotIn("args", template)

    def test_run_container_with_dependency_implicit_params_passing(self):
        output_path = "/mnt/hello_world.txt"

        def producer(step_name):
            output_place = couler.create_parameter_artifact(
                path=output_path, is_global=True
            )
            return couler.run_container(
                image="docker/whalesay:latest",
                args=["echo -n hello world > %s" % output_place.path],
                command=["bash", "-c"],
                output=output_place,
                step_name=step_name,
            )

        def consumer(step_name):
            couler.run_container(
                image="docker/whalesay:latest",
                command=["cowsay"],
                step_name=step_name,
            )

        couler.set_dependencies(
            lambda: producer(step_name="A"), dependencies=None
        )
        couler.set_dependencies(
            lambda: consumer(step_name="B"), dependencies=["A"]
        )

        wf = couler.workflow_yaml()
        template = wf["spec"]["templates"][1]
        # Check input parameters for step A
        self.assertEqual(
            template["inputs"]["parameters"], [{"name": "para-A-0"}]
        )
        # Check output parameters for step A
        self.assertEqual(
            output_path,
            template["outputs"]["parameters"][0]["valueFrom"]["path"],
        )
        self.assertEqual(
            "global-" + template["outputs"]["parameters"][0]["name"],
            template["outputs"]["parameters"][0]["globalName"],
        )
        params = wf["spec"]["templates"][0]["dag"]["tasks"][1]["arguments"][
            "parameters"
        ][0]
        self.assertEqual(params["name"], "para-B-0")
        self.assertTrue(
            '"{{workflow.outputs.parameters.output-id-' in params["value"]
        )
        # Check automatically created emptyDir volume and volume mount
        self.assertEqual(
            template["volumes"], [{"emptyDir": {}, "name": "couler-out-dir-0"}]
        )
        self.assertEqual(
            template["container"]["volumeMounts"],
            [
                OrderedDict(
                    [("name", "couler-out-dir-0"), ("mountPath", "/mnt")]
                )
            ],
        )

        # Check input parameters for step B
        template = wf["spec"]["templates"][2]
        self.assertEqual(
            template["inputs"]["parameters"], [{"name": "para-B-0"}]
        )

    def test_set_dependencies_with_exit_handler(self):
        def producer():
            return couler.run_container(
                image="docker/whalesay:latest",
                args=["echo -n hello world"],
                command=["bash", "-c"],
                step_name="A",
            )

        def consumer():
            return couler.run_container(
                image="docker/whalesay:latest",
                command=["cowsay"],
                step_name="B",
            )

        def exit_handler_succeeded():
            return couler.run_container(
                image="docker/whalesay:latest",
                command=["cowsay"],
                step_name="success-exit",
            )

        def exit_handler_failed():
            return couler.run_container(
                image="docker/whalesay:latest",
                command=["cowsay"],
                step_name="failure-exit",
            )

        couler.set_dependencies(lambda: producer(), dependencies=None)
        couler.set_dependencies(lambda: consumer(), dependencies=["A"])
        couler.set_exit_handler(
            couler.WFStatus.Succeeded, exit_handler_succeeded
        )
        couler.set_exit_handler(couler.WFStatus.Failed, exit_handler_failed)

        wf = couler.workflow_yaml()
        self.assertEqual(wf["spec"]["onExit"], "exit-handler")
        expected_container_spec = (
            "container",
            OrderedDict(
                [("image", "docker/whalesay:latest"), ("command", ["cowsay"])]
            ),
        )
        self.assertEqual(
            wf["spec"]["templates"][3],
            OrderedDict([("name", "success-exit"), expected_container_spec]),
        )
        self.assertEqual(
            wf["spec"]["templates"][4],
            OrderedDict([("name", "failure-exit"), expected_container_spec]),
        )
        self.assertEqual(
            wf["spec"]["templates"][5],
            {
                "name": "exit-handler",
                "steps": [
                    [
                        OrderedDict(
                            [
                                ("name", "success-exit"),
                                ("template", "success-exit"),
                                ("when", "{{workflow.status}} == Succeeded"),
                            ]
                        )
                    ],
                    [
                        OrderedDict(
                            [
                                ("name", "failure-exit"),
                                ("template", "failure-exit"),
                                ("when", "{{workflow.status}} == Failed"),
                            ]
                        )
                    ],
                ],
            },
        )

    def test_create_job(self):
        success_condition = "status.succeeded > 0"
        failure_condition = "status.failed > 3"
        # Null manifest
        with self.assertRaises(ValueError):
            couler.run_job(
                manifest=None,
                success_condition=success_condition,
                failure_condition=failure_condition,
            )
        # Have a manifest
        manifest = """
        apiVersion: batch/v1
        kind: Job
        metadata:
          generateName: rand-num-
        spec:
          template:
            spec:
              containers:
              - name: rand
                image: python:3.6
                command: ["python random_num.py"]
        """
        for set_owner in (True, False):
            couler.run_job(
                manifest=manifest,
                success_condition=success_condition,
                failure_condition=failure_condition,
                set_owner_reference=set_owner,
            )
            self.assertEqual(len(couler.workflow.templates), 1)
            template = couler.workflow.get_template(
                "test-create-job"
            ).to_dict()
            resource = template["resource"]
            self.assertEqual(template["name"], "test-create-job")
            self.assertEqual(resource["action"], "create")
            self.assertEqual(
                resource["setOwnerReference"], "true" if set_owner else "false"
            )
            self.assertEqual(resource["successCondition"], success_condition)
            self.assertEqual(resource["failureCondition"], failure_condition)
            self.assertEqual(resource["manifest"], manifest)
            couler._cleanup()

    def test_run_job_with_dependency_implicit_params_passing_from_container(
        self
    ):
        success_condition = "status.succeeded > 0"
        failure_condition = "status.failed > 3"
        manifest = """
                apiVersion: batch/v1
                kind: Job
                metadata:
                  generateName: rand-num-
                spec:
                  template:
                    spec:
                      containers:
                      - name: rand
                        image: python:3.6
                        command: ["python random_num.py"]
                """

        output_path = "/mnt/hello_world.txt"

        def producer(step_name):
            output_place = couler.create_parameter_artifact(path=output_path)
            return couler.run_container(
                image="docker/whalesay:latest",
                args=["echo -n hello world > %s" % output_place.path],
                command=["bash", "-c"],
                output=output_place,
                step_name=step_name,
            )

        def consumer(step_name):
            couler.run_job(
                manifest=manifest,
                success_condition=success_condition,
                failure_condition=failure_condition,
                step_name=step_name,
                env={"k1": "v1"},
            )

        couler.set_dependencies(
            lambda: producer(step_name="A"), dependencies=None
        )
        couler.set_dependencies(
            lambda: consumer(step_name="B"), dependencies=["A"]
        )
        self.assertEqual(len(couler.workflow.templates), 2)
        wf = couler.workflow_yaml()
        # Check input and output parameters for step A
        template = wf["spec"]["templates"][1]
        self.assertEqual(
            template["inputs"]["parameters"], [{"name": "para-A-0"}]
        )
        self.assertEqual(
            output_path,
            template["outputs"]["parameters"][0]["valueFrom"]["path"],
        )
        # Check env for step B
        manifest_dict = yaml.safe_load(
            wf["spec"]["templates"][2]["resource"]["manifest"]
        )
        self.assertEqual(
            manifest_dict["spec"]["env"][0], {"name": "k1", "value": "v1"}
        )
        envs = manifest_dict["spec"]["env"][1]
        self.assertEqual(envs["name"], "couler.inferred_outputs.0")
        self.assertTrue(
            "{{tasks.A.outputs.parameters.output-id-" in envs["value"]
        )

    def test_run_job_with_dependency_implicit_params_passing_from_job(self):
        success_condition = "status.succeeded > 0"
        failure_condition = "status.failed > 3"
        manifest = """
                apiVersion: batch/v1
                kind: Job
                metadata:
                  generateName: rand-num-
                spec:
                  template:
                    spec:
                      containers:
                      - name: rand
                        image: python:3.6
                        command: ["python random_num.py"]
                """

        def producer(step_name):
            couler.run_job(
                manifest=manifest,
                success_condition=success_condition,
                failure_condition=failure_condition,
                step_name=step_name,
            )

        def consumer(step_name):
            return couler.run_container(
                image="docker/whalesay:latest",
                command=[
                    "bash",
                    "-c",
                    "echo '{{inputs.parameters.para-B-0}}'",
                ],
                step_name=step_name,
            )

        couler.set_dependencies(
            lambda: producer(step_name="A"), dependencies=None
        )
        couler.set_dependencies(
            lambda: consumer(step_name="B"), dependencies=["A"]
        )
        self.assertEqual(len(couler.workflow.templates), 2)
        wf = couler.workflow_yaml()
        # Check task for step B in dag tasks
        template = wf["spec"]["templates"][0]
        self.assertEqual(
            [
                {
                    "value": '"{{tasks.A.outputs.parameters.job-id}}"',
                    "name": "para-B-0",
                },
                {
                    "value": '"{{tasks.A.outputs.parameters.job-name}}"',
                    "name": "para-B-1",
                },
                {
                    "value": '"{{tasks.A.outputs.parameters.job-obj}}"',
                    "name": "para-B-2",
                },
            ],
            template["dag"]["tasks"][1]["arguments"]["parameters"],
        )
        # Check output parameters for step A
        template = wf["spec"]["templates"][1]
        self.assertEqual(
            [
                {
                    "name": "job-name",
                    "valueFrom": {"jsonPath": '"{.metadata.name}"'},
                },
                {
                    "name": "job-id",
                    "valueFrom": {"jsonPath": '"{.metadata.uid}"'},
                },
                {"name": "job-obj", "valueFrom": {"jqFilter": '"."'}},
            ],
            template["outputs"]["parameters"],
        )
        # Check input parameters for step A
        template = wf["spec"]["templates"][2]
        self.assertEqual(
            [{"name": "para-B-0"}, {"name": "para-B-1"}, {"name": "para-B-2"}],
            template["inputs"]["parameters"],
        )

    def _verify_script_body(
        self, script_to_check, image, command, source, env
    ):
        self.assertEqual(script_to_check.get("image", None), image)
        self.assertEqual(script_to_check.get("command", None), command)
        self.assertEqual(script_to_check.get("source", None), source)
        self.assertEqual(script_to_check.get("env", None), env)


if __name__ == "__main__":
    unittest.main()
