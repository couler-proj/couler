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

couler.config_workflow(name="pytest")


def producer():
    output_place = couler.create_parameter_artifact(
        path="/mnt/hello_world.txt"
    )
    return couler.run_container(
        image="docker/whalesay:latest",
        args=["echo -n hello world > %s" % output_place.path],
        command=["bash", "-c"],
        output=output_place,
    )


def consumer(message):
    couler.run_container(
        image="docker/whalesay:latest", command=["cowsay"], args=[message]
    )


class StepOutputTest(ArgoYamlTest):
    def test_producer_consumer(self):
        messge = producer()
        consumer(messge)
        self.check_argo_yaml("output_golden_1.yaml")

    def test_multiple_outputs(self):
        def producer_two():
            output_one = couler.create_parameter_artifact(
                path="/mnt/place_one.txt"
            )
            output_two = couler.create_parameter_artifact(
                path="/mnt/place_two.txt"
            )
            c1 = "echo -n output one > %s" % output_one.path
            c2 = "echo -n output tw0 > %s" % output_two.path
            command = "%s && %s" % (c1, c2)
            return couler.run_container(
                image="docker/whalesay:latest",
                args=command,
                output=[output_one, output_two],
                command=["bash", "-c"],
            )

        def consume_two(message):
            couler.run_container(
                image="docker/whalesay:latest",
                command=["cowsay"],
                args=[message],
            )

        messages = producer_two()
        consume_two(messages)
        self.check_argo_yaml("output_golden_2.yaml")
