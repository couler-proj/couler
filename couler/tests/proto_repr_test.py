import unittest

import couler.argo as couler
from couler.core import states
from couler.core.proto_repr import get_default_proto_workflow


class ProtoReprTest(unittest.TestCase):
    def tearDown(self):
        couler._cleanup()

    def test_script_step(self):
        def echo():
            print("echo")

        couler.run_script(
            image="docker/whalesay:latest",
            source=echo,
            resources={"cpu": "2", "memory": "1Gi"},
        )
        proto_wf = get_default_proto_workflow()
        s = proto_wf.steps[0].steps[0]
        self.assertFalse(s.HasField("resource_spec"))
        self.assertEqual(s.script, '\nprint("echo")\n')
        self.assertEqual(s.container_spec.resources["cpu"], "2")

    def test_canned_step(self):
        couler.run_canned_step(name="test", args={"k1": "v1", "k2": "v2"})
        proto_wf = get_default_proto_workflow()
        s = proto_wf.steps[0].steps[0]
        self.assertEqual(s.canned_step_spec.name, "test")
        self.assertEqual(s.canned_step_spec.args, {"k1": "v1", "k2": "v2"})

    def test_when(self):
        def random_code():
            import random

            res = "heads" if random.randint(0, 1) == 0 else "tails"
            print(res)

        def heads():
            return couler.run_container(
                image="alpine:3.6", command=["sh", "-c", 'echo "it was heads"']
            )

        def tails():
            return couler.run_container(
                image="alpine:3.6", command=["sh", "-c", 'echo "it was tails"']
            )

        result = couler.run_script(
            image="python:alpine3.6", source=random_code
        )
        couler.when(couler.equal(result, "heads"), lambda: heads())
        couler.when(couler.equal(result, "tails"), lambda: tails())
        proto_wf = get_default_proto_workflow()
        step_heads = proto_wf.steps[1].steps[0]
        # condition is like: "{{steps.test-when-550.outputs.result}} == heads"
        self.assertTrue(step_heads.when.startswith("{{steps.test-when-"))
        self.assertTrue(step_heads.when.endswith(".outputs.result}} == heads"))

    def test_exit_handler(self):
        def send_mail():
            return couler.run_container(
                image="alpine:3.6", command=["echo", "send mail"]
            )

        couler.run_container(image="alpine:3.6", command=["exit", "1"])
        couler.set_exit_handler(couler.WFStatus.Failed, send_mail)
        proto_wf = get_default_proto_workflow()
        self.assertEqual(len(proto_wf.exit_handler_steps), 1)
        s = proto_wf.exit_handler_steps[0]
        self.assertEqual(s.when, "{{workflow.status}} == Failed")

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
        s = proto_wf.steps[0].steps[0]
        t = proto_wf.templates[s.tmpl_name]
        self.assertEqual(s.container_spec.image, "docker/whalesay:latest")
        self.assertTrue(t.outputs[0].artifact.name.startswith("output-oss"))
        self.assertEqual(t.outputs[0].artifact.local_path, "/home/t1.txt")
        self.assertEqual(t.outputs[0].artifact.endpoint, "xyz.com")
        self.assertEqual(t.outputs[0].artifact.bucket, "test-bucket/")

        self.assertEqual(t.outputs[0].artifact.access_key.key, "accessKey")
        proto_sk = t.outputs[0].artifact.secret_key
        self.assertEqual(proto_sk.key, "secretKey")
        self.assertEqual(
            proto_sk.value, states._secrets[proto_sk.name].data[proto_sk.key]
        )

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
        s = proto_wf.steps[0].steps[0]
        t = proto_wf.templates[s.tmpl_name]
        self.assertFalse(s.HasField("container_spec"))
        self.assertEqual(s.resource_spec.manifest, manifest)
        self.assertEqual(s.resource_spec.success_condition, success_condition)
        self.assertEqual(s.resource_spec.failure_condition, failure_condition)
        self.assertEqual(len(t.outputs), 3)
        self.assertEqual(t.outputs[0].parameter.name, "job-name")


if __name__ == "__main__":
    unittest.main()
