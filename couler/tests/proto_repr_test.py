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
            path="/tmp/t1.txt",
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
        self.assertEqual(s.image, "docker/whalesay:latest")
        self.assertTrue(s.outputs[0].artifact.name.startswith("output-oss"))

        couler._cleanup()


if __name__ == "__main__":
    unittest.main()
