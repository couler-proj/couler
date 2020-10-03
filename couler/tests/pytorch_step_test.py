from io import StringIO

import yaml

import couler.argo as couler
import couler.steps.pytorch as pytorch
from couler.core import utils
from couler.tests.argo_yaml_test import ArgoYamlTest


class PyTorchTestCase(ArgoYamlTest):
    def test_pytorch_train(self):
        access_key_secret = {"access_key": "key1234"}
        secret = couler.create_secret(secret_data=access_key_secret)

        pytorch.train(
            num_workers=3,
            image="pytorch:1.13",
            command="python pytorch.py",
            worker_resources="cpu=0.5,memory=1024",
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
        self.assertEqual(template1["name"], "test-pytorch-train")
        resource = template1["resource"]
        self.assertEqual(resource["action"], "create")
        self.assertEqual(resource["setOwnerReference"], "true")
        self.assertEqual(
            resource["successCondition"],
            "status.pytorchReplicaStatuses.Worker.succeeded > 0",
        )
        self.assertEqual(
            resource["failureCondition"],
            "status.pytorchReplicaStatuses.Worker.failed > 0",
        )
        # Check the PyTorchJob spec
        pytorch_job = yaml.load(
            StringIO(resource["manifest"]), Loader=yaml.FullLoader
        )
        self.assertEqual(pytorch_job["kind"], "PyTorchJob")
        self.assertEqual(pytorch_job["spec"]["cleanPodPolicy"], "Running")

        master = pytorch_job["spec"]["pytorchReplicaSpecs"]["Master"]
        self.assertEqual(master["replicas"], 1)
        chief_container = master["template"]["spec"]["containers"][0]
        self.assertEqual(chief_container["env"][0]["name"], "access_key")
        self.assertEqual(
            chief_container["env"][0]["valueFrom"]["secretKeyRef"]["name"],
            secret_yaml["metadata"]["name"],
        )

        worker = pytorch_job["spec"]["pytorchReplicaSpecs"]["Worker"]
        self.assertEqual(worker["replicas"], 3)
        self.assertEqual(worker["restartPolicy"], "OnFailure")
        self.assertEqual(len(worker["template"]["spec"]["containers"]), 1)
        worker_container = worker["template"]["spec"]["containers"][0]
        self.assertEqual(worker_container["image"], "pytorch:1.13")
        self.assertEqual(worker_container["command"], "python pytorch.py")

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
