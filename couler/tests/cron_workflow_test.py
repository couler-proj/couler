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

_test_data_dir = "test_data"


class CronJobTest(ArgoYamlTest):
    def test_cron_workflow(self):
        def tails():
            return couler.run_container(
                image="python:3.6",
                command=["bash", "-c", 'echo "run schedule job"'],
            )

        tails()

        # schedule to run at one minute past midnight (00:01) every day
        cron_config = {"schedule": "1 0 * * *", "suspend": "false"}

        couler.config_workflow(name="pytest", cron_config=cron_config)

        self.check_argo_yaml("cron_workflow_golden.yaml")
