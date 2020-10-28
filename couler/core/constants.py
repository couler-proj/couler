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

from enum import Enum


class WorkflowCRD(object):
    PLURAL = "workflows"
    KIND = "Workflow"
    GROUP = "argoproj.io"
    VERSION = "v1alpha1"
    NAME_MAX_LENGTH = 45
    NAME_PATTERN = r"[a-z]([-a-z0-9]*[a-z0-9])?"


class CronWorkflowCRD(WorkflowCRD):
    PLURAL = "cronworkflows"
    KIND = "CronWorkflow"


class ImagePullPolicy(Enum):
    IfNotPresent = "IfNotPresent"
    Always = "Always"
    Never = "Never"

    @classmethod
    def valid(cls, value: str) -> bool:
        return value in cls.__members__

    @classmethod
    def values(cls) -> list:
        return list(cls.__members__.keys())


class WFStatus(Enum):
    Succeeded = "Succeeded"
    Failed = "Failed"
    Error = "Error"
