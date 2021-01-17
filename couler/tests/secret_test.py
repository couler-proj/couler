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

import couler.argo as couler
from couler.core import utils
from couler.tests.argo_yaml_test import ArgoYamlTest

_test_data_dir = "test_data"
couler.config_workflow(name="pytest")


class SecretTest(ArgoYamlTest):
    def test_create_secret(self):
        # First job with secret1
        user_info = {"uname": "abc", "passwd": "def"}
        secret1 = couler.create_secret(secret_data=user_info, name="dummy1")
        couler.run_container(
            image="python:3.6", secret=secret1, command="echo $uname"
        )

        # Second job with secret2
        access_key = {"access_key": "key1234", "access_value": "value5678"}
        secret2 = couler.create_secret(
            secret_data=access_key, namespace="test", name="dummy2"
        )
        couler.run_container(
            image="python:3.6", secret=secret2, command="echo $access_value"
        )

        # Check the secret yaml
        self.assertEqual(len(couler.states._secrets), 2)
        secret1_yaml = couler.states._secrets[secret1].to_yaml()
        secret2_yaml = couler.states._secrets[secret2].to_yaml()

        self.assertEqual(secret1_yaml["metadata"]["namespace"], "default")
        self.assertEqual(secret1_yaml["metadata"]["name"], "dummy1")
        self.assertEqual(len(secret1_yaml["data"]), 2)
        self.assertEqual(
            secret1_yaml["data"]["uname"], utils.encode_base64("abc")
        )
        self.assertEqual(
            secret1_yaml["data"]["passwd"], utils.encode_base64("def")
        )

        self.assertEqual(secret2_yaml["metadata"]["namespace"], "test")
        self.assertEqual(secret2_yaml["metadata"]["name"], "dummy2")
        self.assertEqual(len(secret2_yaml["data"]), 2)
        self.assertEqual(
            secret2_yaml["data"]["access_key"], utils.encode_base64("key1234")
        )
        self.assertEqual(
            secret2_yaml["data"]["access_value"],
            utils.encode_base64("value5678"),
        )

    def _verify_script_body(
        self, script_to_check, image, command, source, env
    ):
        if env is None:
            env = utils.convert_dict_to_env_list(
                {
                    "NVIDIA_VISIBLE_DEVICES": "",
                    "NVIDIA_DRIVER_CAPABILITIES": "",
                }
            )
        else:
            env.append(
                utils.convert_dict_to_env_list(
                    {
                        "NVIDIA_VISIBLE_DEVICES": "",
                        "NVIDIA_DRIVER_CAPABILITIES": "",
                    }
                )
            )
        self.assertEqual(script_to_check.get("image", None), image)
        self.assertEqual(script_to_check.get("command", None), command)
        self.assertEqual(script_to_check.get("source", None), source)
        self.assertEqual(script_to_check.get("env", None), env)

    def test_create_secrete_duplicate(self):
        def job_1():
            user_info = {"uname": "abc", "passwd": "def"}
            secret1 = couler.create_secret(secret_data=user_info, dry_run=True)
            couler.run_container(
                image="python:3.6", secret=secret1, command="echo $uname"
            )

        def job_2():
            user_info = {"uname": "abc", "passwd": "def"}
            secret1 = couler.create_secret(secret_data=user_info, dry_run=True)
            couler.run_container(
                image="python:3.6", secret=secret1, command="echo $uname"
            )

        job_1()
        job_2()

        self.check_argo_yaml("secret_golden.yaml")
