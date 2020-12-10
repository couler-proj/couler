import unittest

import couler.argo as couler
from couler.core.proto_repr import get_default_proto_workflow


class ProtoReprTest(unittest.TestCase):
    def test_script_step(self):
        def echo():
            print("echo")

        couler.run_script(image="docker/whalesay:latest", source=echo)
        proto_wf = get_default_proto_workflow()
        s = proto_wf.steps[0]
        self.assertEqual(s.script, '\nprint("echo")\n')

        couler._cleanup()

    def test_output_oss_artifact(self):
        # the content of local file would be uploaded to OSS
        output_artifact = couler.create_oss_artifact(
            path="/home/t1.txt",
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
        proto_wf = get_default_proto_workflow()
        s = proto_wf.steps[0]
        self.assertEqual(s.container_spec.image, "docker/whalesay:latest")
        self.assertTrue(s.outputs[0].artifact.name.startswith("output-oss"))

        couler._cleanup()

    def test_run_job(self):
        success_condition = "status.succeeded > 0"
        failure_condition = "status.failed > 3"
        manifest = """apiVersion: batch/v1
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
        couler.run_job(
            manifest=manifest,
            success_condition=success_condition,
            failure_condition=failure_condition,
            step_name="test_run_job",
        )
        proto_wf = get_default_proto_workflow()
        s = proto_wf.steps[0]
        self.assertEqual(s.container_spec.image, "python:3.6")

        couler._cleanup()


if __name__ == "__main__":
    unittest.main()
