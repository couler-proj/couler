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

from collections import OrderedDict

from couler.core import states, utils


def config_workflow(
    name=None,
    user_id=None,
    timeout=None,
    time_to_clean=None,
    cluster_config_file=None,
    cron_config=None,
    service_account=None,
):
    """
    Config some workflow-level information.
    :param name: name of the workflow.
    :param user_id: user information.
    :param timeout: maximum running time(seconds).
    :param time_to_clean: time to keep the workflow after completed(seconds).
    :param cluster_config_file: cluster specific config
    :param cron_config: for cron scheduling
    :param service_account: name of the Kubernetes ServiceAccount which
        runs this workflow
    :return:
    """
    if name is not None:
        states.workflow.name = name

    if user_id is not None:
        states.workflow.user_id = user_id

    if timeout is not None:
        states.workflow.timeout = timeout

    if time_to_clean is not None:
        states.workflow.clean_ttl = time_to_clean

    if cluster_config_file is not None:
        import os

        os.environ["couler_cluster_config"] = cluster_config_file
        states.workflow.cluster_config = utils.load_cluster_config()

    if cron_config is not None:
        if isinstance(cron_config, OrderedDict):
            raise SyntaxError("Cron config would be a dict")

        if "schedule" not in cron_config:
            raise SyntaxError("require the cron schedule")

        schedule = cron_config["schedule"]
        concurrency_policy = cron_config.get("concurrency_policy", "Allow")
        successful_jobs_history_limit = cron_config.get(
            "successful_jobs_history_limit", 3
        )
        failed_jobs_history_limit = cron_config.get(
            "failed_jobs_history_limit", 1
        )
        starting_deadline_seconds = cron_config.get(
            "starting_deadline_seconds", 10
        )
        suspend = cron_config.get("suspend", "false")
        timezone = cron_config.get("timezone", "Asia/Shanghai")
        _config_cron_workflow(
            schedule,
            concurrency_policy,
            successful_jobs_history_limit,
            failed_jobs_history_limit,
            starting_deadline_seconds,
            suspend,
            timezone,
        )

    if service_account is not None:
        states.workflow.service_account = service_account


def _config_cron_workflow(
    schedule,
    concurrency_policy='"Allow"',  # Default to "Allow"
    successful_jobs_history_limit=3,  # Default 3
    failed_jobs_history_limit=1,  # Default 1
    starting_deadline_seconds=10,
    suspend="false",
    timezone="Asia/Shanghai",  # Default to Beijing time
):
    """
    Config the CronWorkflow, see example
    https://github.com/argoproj/argo/blob/master/docs/cron-workflows.md
    """

    cron_config = {
        "schedule": schedule,
        "concurrencyPolicy": concurrency_policy,
        "successfulJobsHistoryLimit": successful_jobs_history_limit,
        "failedJobsHistoryLimit": failed_jobs_history_limit,
        "startingDeadlineSeconds": starting_deadline_seconds,
        "suspend": suspend,
        "timezone": timezone,
    }

    states.workflow.config_cron_workflow(cron_config)
