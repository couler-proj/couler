import unittest
import couler.argo as couler


class DaemonStepTest(unittest.TestCase):
    def setUp(self) -> None:
        couler._cleanup()

    def test_run_daemon_container(self):
        self.assertEqual(len(couler.workflow.templates), 0)
        couler.run_container(
            image="python:3.6", command="echo $uname", daemon=True
        )
        self.assertEqual(len(couler.workflow.templates), 1)
        template = couler.workflow.get_template(
            "test-run-daemon-container"
        ).to_dict()
        self.assertEqual("test-run-daemon-container", template["name"])
        self.assertTrue(template["daemon"])
        self.assertEqual("python:3.6", template["container"]["image"])
        self.assertEqual(["echo $uname"], template["container"]["command"])

    def test_run_daemon_script(self):
        self.assertEqual(len(couler.workflow.templates), 0)
        couler.run_script(
            image="python:3.6", command="bash", source="ls", daemon=True
        )
        self.assertEqual(len(couler.workflow.templates), 1)
        template = couler.workflow.get_template(
            "test-run-daemon-script"
        ).to_dict()
        self.assertEqual("test-run-daemon-script", template["name"])
        self.assertTrue(template["daemon"])
        self.assertEqual("python:3.6", template["script"]["image"])
        self.assertEqual(["bash"], template["script"]["command"])
        self.assertEqual("ls", template["script"]["source"])
