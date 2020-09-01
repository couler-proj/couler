import json
import os
import re
import unittest

import pyaml
import yaml

import couler.argo as couler

_test_data_dir = "test_data"


class ArgoYamlTest(unittest.TestCase):
    def setUp(self):
        couler._cleanup()

    def tearDown(self):
        couler._cleanup()

    @staticmethod
    def mock_dict(x, mock_str="pytest"):
        # The following fields are overwritten so we won't be
        # comparing them. This is to avoid issues caused by
        # different versions of pytest.
        if "generateName" in x["metadata"]:
            x["metadata"]["generateName"] = mock_str
        x["spec"]["entrypoint"] = mock_str
        if "templates" in x["spec"]:
            x["spec"]["templates"][0]["name"] = mock_str
        return x

    def check_argo_yaml(self, expected_fn):
        test_data_dir = os.path.join(os.path.dirname(__file__), _test_data_dir)
        with open(os.path.join(test_data_dir, expected_fn), "r") as f:
            expected = yaml.safe_load(f)
        output = yaml.safe_load(
            pyaml.dump(couler.workflow_yaml(), string_val_style="plain")
        )

        def dump(x):
            x = re.sub(
                r"-[0-9]*", "-***", json.dumps(self.mock_dict(x), indent=2)
            )
            return x

        output_j, expected_j = dump(output), dump(expected)

        self.maxDiff = None
        self.assertEqual(output_j, expected_j)

    def create_callable_cls(self, func):
        class A:
            def a(self, *args):
                return func(*args)

            @classmethod
            def b(cls, *args):
                return func(*args)

            @staticmethod
            def c(*args):
                return func(*args)

            def __call__(self, *args):
                return func(*args)

        return A
