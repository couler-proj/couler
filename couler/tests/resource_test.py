import os
import pyaml
import yaml
import couler.argo as couler
from couler.tests.argo_yaml_test import ArgoYamlTest


class ResourceTest(ArgoYamlTest):
    def test_resource_setup(self):
        couler.run_container(
            image="docker/whalesay",
            command=["cowsay"],
            args=["resource test"],
            resources={"cpu": "1", "memory": "100Mi"},
        )
        # Because test environment between local and CI is different,
        # we can not compare the YAML directly.
        _test_data_dir = "test_data"
        test_data_dir = os.path.join(os.path.dirname(__file__), _test_data_dir)
        with open(
            os.path.join(test_data_dir, "resource_config_golden.yaml"), "r"
        ) as f:
            expected = yaml.safe_load(f)
        output = yaml.safe_load(
            pyaml.dump(couler.workflow_yaml(), string_val_style="plain")
        )
        _resources = output["spec"]["templates"][1]["container"]["resources"]
        _expected_resources = expected["spec"]["templates"][1]["container"][
            "resources"
        ]

        self.assertEqual(_resources, _expected_resources)
        couler._cleanup()
