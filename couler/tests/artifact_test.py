import couler.argo as couler
from couler.tests.argo_yaml_test import ArgoYamlTest

_test_data_dir = "test_data"
couler.config_workflow(name="pytest")


class ArtifactTest(ArgoYamlTest):
    def setUp(self):
        couler._cleanup()

    def tearDown(self):
        couler._cleanup()

    def _oss_check_helper(self, artifact):
        self.assertIn("output-oss", artifact["name"])
        self.assertEqual("/tmp/t1.txt", artifact["path"])
        oss_config = artifact["oss"]
        self.assertIsNotNone(oss_config)
        self.assertEqual(oss_config["endpoint"], "xyz.com")
        self.assertEqual(oss_config["bucket"], "anttest/")
        self.assertEqual(oss_config["key"], "osspath/t1")
        self.assertEqual(oss_config["accessKeySecret"]["key"], "accessKey")
        self.assertEqual(oss_config["secretKeySecret"]["key"], "secretKey")

    def test_output_oss_artifact(self):
        # the content of local file would be uploaded to OSS
        output_artifact = couler.create_oss_artifact(
            path="/tmp/t1.txt",
            bucket="anttest/",
            accesskey_id="abcde",
            accesskey_secret="abc12345",
            key="osspath/t1",
            endpoint="xyz.com",
        )
        couler.run_container(
            image="docker/whalesay:latest",
            args=["echo -n hello world > %s" % output_artifact.path],
            command=["bash", "-c"],
            output=output_artifact,
        )

        wf = couler.workflow_yaml()
        template = wf["spec"]["templates"][1]
        artifact = template["outputs"]["artifacts"][0]
        self._oss_check_helper(artifact)
        couler._cleanup()

    def test_input_oss_artifact(self):
        input_artifact = couler.create_oss_artifact(
            path="/tmp/t1.txt",
            bucket="anttest/",
            accesskey_id="abcde",
            accesskey_secret="abc12345",
            key="osspath/t1",
            endpoint="xyz.com",
        )

        # read the content from an OSS bucket
        couler.run_container(
            image="docker/whalesay:latest",
            args=["cat %s" % input_artifact.path],
            command=["bash", "-c"],
            input=input_artifact,
        )

        wf = couler.workflow_yaml()
        template = wf["spec"]["templates"][1]
        artifact = template["inputs"]["artifacts"][0]
        self._oss_check_helper(artifact)
        couler._cleanup()

    def test_artifact_passing(self):
        def producer():
            output_artifact = couler.create_oss_artifact(
                path="/tmp/t1.txt",
                bucket="anttest/",
                accesskey_id="abcde",
                accesskey_secret="abc12345",
                key="osspath/t1",
                endpoint="xyz.com",
            )

            outputs = couler.run_container(
                image="docker/whalesay:latest",
                args=["echo -n hello world > %s" % output_artifact.path],
                command=["bash", "-c"],
                output=output_artifact,
            )

            return outputs

        def consumer(inputs):
            # read the content from an OSS bucket
            couler.run_container(
                image="docker/whalesay:latest",
                args=inputs,
                command=[("cat %s" % inputs[0].path)],
            )

        outputs = producer()
        consumer(outputs)

        wf = couler.workflow_yaml()
        template = wf["spec"]["templates"][1]
        artifact = template["outputs"]["artifacts"][0]
        self._oss_check_helper(artifact)
        template = wf["spec"]["templates"][2]
        artifact = template["inputs"]["artifacts"][0]
        self._oss_check_helper(artifact)
        couler._cleanup()

    def test_set_dependencies_with_upstream(self):
        def producer(step_name):
            output_artifact = couler.create_oss_artifact(
                path="/tmp/t1.txt",
                bucket="anttest/",
                accesskey_id="abcde",
                accesskey_secret="abc12345",
                key="osspath/t1",
                endpoint="xyz.com",
            )

            outputs = couler.run_container(
                image="docker/whalesay:latest",
                args=["echo -n hello world > %s" % output_artifact.path],
                command=["bash", "-c"],
                output=output_artifact,
                step_name=step_name,
            )

            return outputs

        def consumer(step_name):
            # read the content from an OSS bucket
            inputs = couler.get_step_output(step_name="A")
            couler.run_container(
                image="docker/whalesay:latest",
                args=inputs,
                command=[("cat %s" % inputs[0].path)],
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
        artifact = template["outputs"]["artifacts"][0]
        self._oss_check_helper(artifact)
        template = wf["spec"]["templates"][2]
        artifact = template["inputs"]["artifacts"][0]
        self._oss_check_helper(artifact)
        couler._cleanup()

    def test_set_dependencies_with_passing_artifact_implicitly(self):

        default_path = "/tmp/t1.txt"

        def producer(step_name):
            output_artifact = couler.create_oss_artifact(
                default_path,
                bucket="anttest/",
                accesskey_id="abcde",
                accesskey_secret="abc12345",
                key="osspath/t1",
                endpoint="xyz.com",
            )

            outputs = couler.run_container(
                image="docker/whalesay:latest",
                args=["echo -n hello world > %s" % output_artifact.path],
                command=["bash", "-c"],
                output=output_artifact,
                step_name=step_name,
            )

            return outputs

        def consumer(step_name):
            # read the content from an OSS bucket
            # inputs = couler.get_step_output(step_name="A")
            couler.run_container(
                image="docker/whalesay:latest",
                args=["--test 1"],
                command=[("cat %s" % default_path)],
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
        artifact = template["outputs"]["artifacts"][0]
        self._oss_check_helper(artifact)
        template = wf["spec"]["templates"][2]
        artifact = template["inputs"]["artifacts"][0]
        self._oss_check_helper(artifact)
        couler._cleanup()
