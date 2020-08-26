#!/usr/bin/env bash

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
