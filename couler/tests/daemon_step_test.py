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
from couler.tests.argo_test import ArgoBaseTestCase


class DaemonStepTest(ArgoBaseTestCase):
    def setUp(self) -> None:
        couler._cleanup()

    def tearDown(self):
        couler._cleanup()

    def test_run_daemon_container(self):
        self.assertEqual(len(couler.workflow.templates), 0)
        couler.run_container(
            image="python:3.6", command="echo $uname", daemon=True
        )
        self.assertEqual(len(couler.workflow.templates), 1)
        template = couler.workflow.get_template(
            "test-run-daemon-container"
        ).to_dict()
        self.assertEqual("test-run-daemon-container", template["name"])
        self.assertTrue(template["daemon"])
        self.assertEqual("python:3.6", template["container"]["image"])
        self.assertEqual(["echo $uname"], template["container"]["command"])

    def test_run_daemon_script(self):
        self.assertEqual(len(couler.workflow.templates), 0)
        couler.run_script(
            image="python:3.6", command="bash", source="ls", daemon=True
        )
        self.assertEqual(len(couler.workflow.templates), 1)
        template = couler.workflow.get_template(
            "test-run-daemon-script"
        ).to_dict()
        self.assertEqual("test-run-daemon-script", template["name"])
        self.assertTrue(template["daemon"])
        self.assertEqual("python:3.6", template["script"]["image"])
        self.assertEqual(["bash"], template["script"]["command"])
        self.assertEqual("ls", template["script"]["source"])
