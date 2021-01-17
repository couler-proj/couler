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

import json
import os
import re

import pyaml
import yaml

import couler.argo as couler
from couler.tests.argo_test import ArgoBaseTestCase

_test_data_dir = "test_data"


class ArgoYamlTest(ArgoBaseTestCase):
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
