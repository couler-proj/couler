from io import StringIO

import yaml

from couler.core import utils
import couler.argo as couler
import couler.steps.tensorflow as tf
from couler.tests.argo_yaml_test import ArgoYamlTest


class TensorflowTestCase(ArgoYamlTest):
    def test_tensorflow_train(self):
        access_key_secret = {"access_key": "key1234"}
        secret = couler.create_secret(secret_data=access_key_secret)

        tf.train(
            num_ps=2,
            num_workers=3,
            image="tensorflow:1.13",
            command="python tf.py",
            no_chief=False,
            worker_resources="cpu=0.5,memory=1024",
            ps_restart_policy="Never",
            worker_restart_policy="OnFailure",
            clean_pod_policy="Running",
            secret=secret,
        )

        secret_yaml = list(couler.states._secrets.values())[0].to_yaml()
        self.assertEqual(
            secret_yaml["data"]["access_key"], utils.encode_base64("key1234")
        )

        wf = couler.workflow_yaml()
        self.assertEqual(len(wf["spec"]["templates"]), 2)
        # Check steps template
        template0 = wf["spec"]["templates"][0]
        self.assertEqual(len(template0["steps"]), 1)
        self.assertEqual(len(template0["steps"][0]), 1)
        # Check train template
        template1 = wf["spec"]["templates"][1]
        self.assertEqual(template1["name"], "test-tensorflow-train")
        resource = template1["resource"]
        self.assertEqual(resource["action"], "create")
        self.assertEqual(resource["setOwnerReference"], "true")
        self.assertEqual(
            resource["successCondition"],
            "status.tfReplicaStatuses.Worker.succeeded > 0",
        )
        self.assertEqual(
            resource["failureCondition"],
            "status.tfReplicaStatuses.Worker.failed > 0",
        )
        # Check the tfjob spec
        tfjob = yaml.load(
            StringIO(resource["manifest"]), Loader=yaml.FullLoader
        )
        self.assertEqual(tfjob["kind"], "TFJob")
        self.assertEqual(tfjob["spec"]["cleanPodPolicy"], "Running")

        chief = tfjob["spec"]["tfReplicaSpecs"]["Chief"]
        self.assertEqual(chief["replicas"], 1)
        chief_container = chief["template"]["spec"]["containers"][0]
        self.assertEqual(chief_container["env"][0]["name"], "access_key")
        self.assertEqual(
            chief_container["env"][0]["valueFrom"]["secretKeyRef"]["name"],
            secret_yaml["metadata"]["name"],
        )

        ps = tfjob["spec"]["tfReplicaSpecs"]["PS"]
        self.assertEqual(ps["replicas"], 2)
        self.assertEqual(ps["restartPolicy"], "Never")
        self.assertEqual(len(ps["template"]["spec"]["containers"]), 1)
        ps_container = ps["template"]["spec"]["containers"][0]
        self.assertEqual(ps_container["image"], "tensorflow:1.13")
        self.assertEqual(ps_container["command"], "python tf.py")

        worker = tfjob["spec"]["tfReplicaSpecs"]["Worker"]
        self.assertEqual(worker["replicas"], 3)
        self.assertEqual(worker["restartPolicy"], "OnFailure")
        self.assertEqual(len(worker["template"]["spec"]["containers"]), 1)
        worker_container = ps["template"]["spec"]["containers"][0]
        self.assertEqual(worker_container["image"], "tensorflow:1.13")
        self.assertEqual(worker_container["command"], "python tf.py")

        worker_container = worker["template"]["spec"]["containers"][0]
        self.assertEqual(worker_container["env"][0]["name"], "access_key")
        self.assertEqual(
            worker_container["env"][0]["valueFrom"]["secretKeyRef"]["name"],
            secret_yaml["metadata"]["name"],
        )
        self.assertEqual(worker_container["resources"]["limits"]["cpu"], 0.5)
        self.assertEqual(
            worker_container["resources"]["limits"]["memory"], 1024
        )
