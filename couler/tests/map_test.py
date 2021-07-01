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


def consume(message):
    return couler.run_container(
        image="docker/whalesay:latest", command=["cowsay"], args=[message]
    )


def consume_m(*other):
    return couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[other[0], other[1]],
    )


class MapTest(ArgoYamlTest):
    def test_map_function(self):

        test_paras = ["t1", "t2", "t3"]
        couler.map(lambda x: consume(x), test_paras)
        wf = couler.workflow_yaml()

        templates = wf["spec"]["templates"]
        self.assertEqual(len(templates), 2)

        # We should have a 'consume' template
        consume_template = templates[1]
        self.assertEqual(consume_template["name"], "consume")
        # Check input parameters
        expected_paras = [{"name": "para-consume-0"}]
        self.assertListEqual(
            consume_template["inputs"]["parameters"], expected_paras
        )
        # Check container
        expected_container = {
            "image": "docker/whalesay:latest",
            "command": ["cowsay"],
            "args": ['"{{inputs.parameters.para-consume-0}}"'],
        }
        self.assertDictEqual(consume_template["container"], expected_container)

        # Check the steps template
        steps_template = templates[0]
        self.assertTrue(steps_template["name"] in ["pytest", "runpy"])
        self.assertEqual(len(steps_template["steps"]), 1)
        self.assertEqual(len(steps_template["steps"][0]), 1)
        map_step = steps_template["steps"][0][0]
        self.assertIn("consume", map_step["name"])
        self.assertEqual(map_step["template"], "consume")
        # Check arguments
        expected_paras = [
            {"name": "para-consume-0", "value": '"{{item.para-consume-0}}"'}
        ]
        self.assertListEqual(
            map_step["arguments"]["parameters"], expected_paras
        )
        # Check withItems
        expected_with_items = [
            {"para-consume-0": "t1"},
            {"para-consume-0": "t2"},
            {"para-consume-0": "t3"},
        ]
        self.assertListEqual(map_step["withItems"], expected_with_items)
        couler._cleanup()

    def test_map_function_callable(self):
        test_paras = ["t1", "t2", "t3"]
        callable_cls = self.create_callable_cls(lambda x: consume(x))
        instance = callable_cls()
        func_names = ["a", "b", "c", "self"]
        for func_name in func_names:
            if func_name == "self":
                couler.map(instance, test_paras)
            else:
                couler.map(getattr(instance, func_name), test_paras)
            expected_with_items = [
                {"para-consume-0": "t1"},
                {"para-consume-0": "t2"},
                {"para-consume-0": "t3"},
            ]
            wf = couler.workflow_yaml()
            templates = wf["spec"]["templates"]
            steps_template = templates[0]
            map_step = steps_template["steps"][0][0]
            self.assertListEqual(map_step["withItems"], expected_with_items)
            couler._cleanup()

    def test_map_function_multiple_arg(self):

        test_paras_1 = ["t1", "t2", "t3"]
        test_paras_2 = ["x1", "x2", "x3"]

        couler.map(lambda x, y: consume_m(x, y), test_paras_1, test_paras_2)
        wf = couler.workflow_yaml()

        templates = wf["spec"]["templates"]
        self.assertEqual(len(templates), 2)

        # We should have a 'consume' template
        consume_template = templates[1]
        self.assertEqual(consume_template["name"], "consume-m")
        # Check input parameters
        expected_paras = [
            {"name": "para-consume-m-0"},
            {"name": "para-consume-m-1"},
        ]
        self.assertListEqual(
            consume_template["inputs"]["parameters"], expected_paras
        )
        # Check container
        expected_container = {
            "image": "docker/whalesay:latest",
            "command": ["cowsay"],
            "args": [
                '"{{inputs.parameters.para-consume-m-0}}"',
                '"{{inputs.parameters.para-consume-m-1}}"',
            ],
        }
        self.assertDictEqual(consume_template["container"], expected_container)
        # Check the steps template
        steps_template = templates[0]
        self.assertTrue(steps_template["name"] in ["pytest", "runpy"])
        self.assertEqual(len(steps_template["steps"]), 1)
        self.assertEqual(len(steps_template["steps"][0]), 1)
        map_step = steps_template["steps"][0][0]
        self.assertIn("consume-m", map_step["name"])
        self.assertEqual(map_step["template"], "consume-m")
        # Check arguments
        expected_paras = [
            {
                "name": "para-consume-m-0",
                "value": '"{{item.para-consume-m-0}}"',
            },
            {
                "name": "para-consume-m-1",
                "value": '"{{item.para-consume-m-1}}"',
            },
        ]
        self.assertListEqual(
            map_step["arguments"]["parameters"], expected_paras
        )
        # Check withItems
        expected_with_items = [
            {"para-consume-m-0": "t1", "para-consume-m-1": "x1"},
            {"para-consume-m-0": "t2", "para-consume-m-1": "x2"},
            {"para-consume-m-0": "t3", "para-consume-m-1": "x3"},
        ]
        self.assertListEqual(map_step["withItems"], expected_with_items)
        couler._cleanup()

    # TODO: Provide new test case without `tf.train`.
    # def test_map_function_with_run_job(self):
    #     couler.map(
    #         lambda x: tf.train(
    #             num_ps=1,
    #             num_workers=1,
    #             command="python /opt/kubeflow/tf_smoke.py",
    #             image="couler/tf-smoke-test:v1.0",
    #             step_name=x,
    #         ),
    #         ["couler-tf-job-0", "couler-tf-job-1"],
    #     )
    #     wf = couler.workflow_yaml()
    #     templates = wf["spec"]["templates"]
    #     self.assertEqual(len(templates), 2)
    #     # Check inner steps template
    #     inner_steps_template = templates[0]["steps"][0][0]
    #     self.assertEqual(
    #         inner_steps_template["arguments"]["parameters"],
    #         [
    #             {
    #                 "name": "couler-tf-job-0-para-name",
    #                 "value": '"{{item.couler-tf-job-0-para-name}}"',
    #             }
    #         ],
    #     )
    #     self.assertEqual(
    #         inner_steps_template["withItems"],
    #         [
    #             {"couler-tf-job-0-para-name": "couler-tf-job-0"},
    #             {"couler-tf-job-0-para-name": "couler-tf-job-1"},
    #         ],
    #     )
    #     # Check training step template
    #     training_template = templates[1]
    #     self.assertEqual(
    #         training_template["inputs"]["parameters"],
    #         [{"name": "couler-tf-job-0-para-name"}],
    #     )
    #     self.assertTrue(
    #         "name: '{{inputs.parameters.couler-tf-job-0-para-name}}'"
    #         in training_template["resource"]["manifest"]
    #     )
    #     couler._cleanup()
