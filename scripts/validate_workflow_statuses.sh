#!/usr/bin/env bash
# Copyright 2020 The Couler Authors. All rights reserved.
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

# We intentionally `set +e` here since we want to allow certain kinds of known failures that can be ignored.
# For example, workflows may not have been created yet so neither `kubectl get workflows` nor
# `kubectl delete workflow` would be successful at earlier stages of this script.
set +e

WF_NAME=$1
CHECK_INTERVAL_SECS=10

function get_workflow_status {
    local wf_status=$(kubectl -n argo get workflow $1 -o jsonpath='{.status.phase}')
    echo ${wf_status}
}

for i in {1..20}; do
    WF_STATUS=$(get_workflow_status ${WF_NAME})

    if [[ "$WF_STATUS" == "Succeeded" ]]; then
      echo "Workflow ${WF_NAME} succeeded."
      exit 0
    elif [[ "$WF_STATUS" == "Failed" ]] ||
        [[ "$WF_STATUS" == "Error" ]]; then
      echo "Workflow ${WF_NAME} failed."
      kubectl -n argo describe workflow ${WF_NAME}
      exit 1
    else
      echo "Workflow ${WF_NAME} status: ${WF_STATUS}. Continue checking..."
      sleep ${CHECK_INTERVAL_SECS}
    fi
done
echo "Workflow ${WF_NAME} timed out."

exit 1
