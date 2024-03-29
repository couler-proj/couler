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
        self.assertEqual("/mnt/t1.txt", artifact["path"])
        oss_config = artifact[couler.ArtifactType.OSS]
        self.assertIsNotNone(oss_config)
        self.assertEqual(oss_config["endpoint"], "xyz.com")
        self.assertEqual(oss_config["bucket"], "test-bucket/")
        self.assertEqual(oss_config["key"], "osspath/t1")
        self.assertEqual(oss_config["accessKeySecret"]["key"], "accessKey")
        self.assertEqual(oss_config["secretKeySecret"]["key"], "secretKey")

    def test_output_oss_artifact(self):
        # the content of local file would be uploaded to OSS
        output_artifact = couler.create_oss_artifact(
            path="/mnt/t1.txt",
            bucket="test-bucket/",
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
            path="/mnt/t1.txt",
            bucket="test-bucket/",
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

    def _s3_check_helper(self, artifact):
        self.assertIn("output-s3", artifact["name"])
        self.assertEqual("/mnt/t1.txt", artifact["path"])
        s3_config = artifact[couler.ArtifactType.S3]
        self.assertIsNotNone(s3_config)
        self.assertEqual(s3_config["endpoint"], "xyz.com")
        self.assertEqual(s3_config["bucket"], "test-bucket/")
        self.assertEqual(s3_config["key"], "s3path/t1")
        self.assertEqual(s3_config["accessKeySecret"]["key"], "accessKey")
        self.assertEqual(s3_config["secretKeySecret"]["key"], "secretKey")
        self.assertEqual(s3_config["insecure"], True)

    def test_output_s3_artifact(self):
        # the content of local file would be uploaded to OSS
        output_artifact = couler.create_s3_artifact(
            path="/mnt/t1.txt",
            bucket="test-bucket/",
            accesskey_id="abcde",
            accesskey_secret="abc12345",
            key="s3path/t1",
            endpoint="xyz.com",
            insecure=True,
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
        self._s3_check_helper(artifact)
        couler._cleanup()

    def test_input_s3_artifact(self):
        input_artifact = couler.create_s3_artifact(
            path="/mnt/t1.txt",
            bucket="test-bucket/",
            accesskey_id="abcde",
            accesskey_secret="abc12345",
            key="s3path/t1",
            endpoint="xyz.com",
            insecure=True,
        )

        # read the content from an S3 bucket
        couler.run_container(
            image="docker/whalesay:latest",
            args=["cat %s" % input_artifact.path],
            command=["bash", "-c"],
            input=input_artifact,
        )

        wf = couler.workflow_yaml()
        template = wf["spec"]["templates"][1]
        artifact = template["inputs"]["artifacts"][0]
        self._s3_check_helper(artifact)
        couler._cleanup()

    def test_artifact_passing(self):
        def producer():
            output_artifact = couler.create_oss_artifact(
                path="/mnt/t1.txt",
                bucket="test-bucket/",
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
        self.assertEqual(len(template["outputs"]["artifacts"]), 1)
        self._oss_check_helper(artifact)
        template = wf["spec"]["templates"][2]
        artifact = template["inputs"]["artifacts"][0]
        self.assertEqual(len(template["inputs"]["artifacts"]), 1)
        self._oss_check_helper(artifact)
        couler._cleanup()

    def test_set_dependencies_with_upstream(self):
        def producer(step_name):
            output_artifact = couler.create_oss_artifact(
                path="/mnt/t1.txt",
                bucket="test-bucket/",
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

        default_path = "/mnt/t1.txt"

        def producer(step_name):
            output_artifact = couler.create_oss_artifact(
                default_path,
                bucket="test-bucket/",
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
