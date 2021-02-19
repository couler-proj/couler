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
from couler.tests.argo_yaml_test import ArgoYamlTest


def random_code():
    import random

    result = "heads" if random.randint(0, 1) == 0 else "tails"
    print(result)


def flip_coin():
    return couler.run_script(image="python:3.6", source=random_code)


class RecursionTest(ArgoYamlTest):
    def test_while(self):
        couler.exec_while(couler.equal("tails"), lambda: flip_coin())
        self.check_argo_yaml("while_golden.yaml")

    def test_while_condition_callable(self):
        cls = self.create_callable_cls(lambda: "tails")
        instance = cls()
        func_names = ["a", "b", "c", "self"]
        for func_name in func_names:
            if func_name == "self":
                couler.exec_while(couler.equal(instance), lambda: flip_coin())
            else:
                couler.exec_while(
                    couler.equal(getattr(instance, func_name)),
                    lambda: flip_coin(),
                )
            self.check_argo_yaml("while_golden.yaml")
            couler._cleanup()

    def test_while_callable(self):
        cls = self.create_callable_cls(lambda: flip_coin())
        instance = cls()
        func_names = ["a", "b", "c", "self"]
        for func_name in func_names:
            if func_name == "self":
                couler.exec_while(couler.equal("tails"), instance)
            else:
                couler.exec_while(
                    couler.equal("tails"), getattr(instance, func_name)
                )

            self.check_argo_yaml("while_golden.yaml")
            couler._cleanup()
