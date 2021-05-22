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
set -e

python -m integration_tests.mpi_example
python -m integration_tests.dag_example
python -m integration_tests.dag_depends_example
python -m integration_tests.flip_coin_example
python -m integration_tests.flip_coin_security_context_example
python -m integration_tests.memoization_example
python -m integration_tests.volume_example

# Validate workflow statuses
kubectl -n argo get workflows
for WF_NAME in $(kubectl -n argo get workflows --no-headers -o custom-columns=":metadata.name")
do
    bash scripts/validate_workflow_statuses.sh ${WF_NAME}
done
