from enum import Enum

# For cpu-only containers, we need to overwrite these envs
OVERWRITE_GPU_ENVS = {
    "NVIDIA_VISIBLE_DEVICES": "",
    "NVIDIA_DRIVER_CAPABILITIES": "",
}


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
