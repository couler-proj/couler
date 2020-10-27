import os
import unittest

import couler.argo as couler


class ArgoTest(unittest.TestCase):
    def test_cluster_config(self):

        couler.config_workflow(
            cluster_config_file=os.path.join(
                os.path.dirname(__file__), "test_data/dummy_cluster_config.py"
            )
        )
        couler.run_container(
            image="docker/whalesay:latest",
            args=["echo -n hello world"],
            command=["bash", "-c"],
            step_name="A",
        )

        wf = couler.workflow_yaml()
        self.assertTrue(wf["spec"]["hostNetwork"])
        self.assertEqual(wf["spec"]["templates"][1]["tolerations"], [])
        couler._cleanup()
