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
import couler.steps.katib as katib
from couler.tests.argo_test import ArgoBaseTestCase

xgb_cmd = """ \
python /opt/katib/train_xgboost.py \
  --train_dataset train.txt \
  --validation_dataset validation.txt \
  --booster gbtree \
  --objective binary:logistic \
"""

xgboost_mainifest_template = """
        apiVersion: batch/v1
        kind: Job
        metadata:
          name: {{{{.Trial}}}}
          namespace: {{{{.NameSpace}}}}
        spec:
          template:
            spec:
              containers:
              - name: {{{{.Trial}}}}
                image: docker.io/katib/xgboost:v0.1
                command:
                - "{command}"
                {{{{- with .HyperParameters}}}}
                {{{{- range .}}}}
                - "{{{{.Name}}}}={{{{.Value}}}}"
                {{{{- end}}}}
                {{{{- end}}}}
              restartPolicy: Never
""".format(
    command=xgb_cmd
)


class KatibTest(ArgoBaseTestCase):
    def test_katib_with_xgboost_training(self):
        katib.run(
            tuning_params=[
                {"name": "max_depth", "type": "int", "range": [2, 10]},
                {"name": "num_round", "type": "int", "range": [50, 100]},
            ],
            objective={
                "type": "maximize",
                "goal": 1.01,
                "metric_name": "accuracy",
            },
            success_condition="status.trialsSucceeded > 4",
            failure_condition="status.trialsFailed > 3",
            algorithm="random",
            raw_template=xgboost_mainifest_template,
            parallel_trial_count=4,
            max_trial_count=16,
            max_failed_trial_count=3,
        )

        wf = couler.workflow_yaml()

        self.assertEqual(len(wf["spec"]["templates"]), 2)
        # Check steps template
        template0 = wf["spec"]["templates"][0]
        self.assertEqual(len(template0["steps"]), 1)
        self.assertEqual(len(template0["steps"][0]), 1)
        # Check train template
        template1 = wf["spec"]["templates"][1]
        self.assertTrue(template1["name"] in ["run", "test-run-python-script"])
