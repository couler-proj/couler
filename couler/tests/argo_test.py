import unittest
from collections import OrderedDict

import yaml

import couler.argo as couler
from couler.core.templates.volume import Volume, VolumeMount
from couler.core.templates.volume_claim import VolumeClaimTemplate


class ArgoTest(unittest.TestCase):
    def setUp(self):
        couler._cleanup()

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
            source="\ncouler._cleanup()\n",
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
            source="\ncouler._cleanup()\n",
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

        wf = couler.workflow_yaml()
        self.assertEqual(wf["spec"]["volumeClaimTemplates"][0], pvc.to_dict())
        self.assertEqual(
            wf["spec"]["templates"][1]["container"]["volumeMounts"][0],
            volume_mount.to_dict(),
        )
        couler._cleanup()

    def test_run_container_with_dependency_implicit_params_passing(self):
        output_path = "/tmp/hello_world.txt"

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
            params["value"]
            in [
                '"{{workflow.outputs.parameters.output-id-133}}"',
                '"{{workflow.outputs.parameters.output-id-134}}"',
            ]
        )
        # Check input parameters for step B
        template = wf["spec"]["templates"][2]
        self.assertEqual(
            template["inputs"]["parameters"], [{"name": "para-B-0"}]
        )
        couler._cleanup()

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
        couler._cleanup()

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

        output_path = "/tmp/hello_world.txt"

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
        couler._cleanup()

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
        couler._cleanup()

    def _verify_script_body(
        self, script_to_check, image, command, source, env
    ):
        self.assertEqual(script_to_check.get("image", None), image)
        self.assertEqual(script_to_check.get("command", None), command)
        self.assertEqual(script_to_check.get("source", None), source)
        self.assertEqual(script_to_check.get("env", None), env)
