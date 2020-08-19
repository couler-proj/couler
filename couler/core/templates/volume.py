from collections import OrderedDict


class Volume(object):
    def __init__(self, name, claim_name):
        self.name = name
        self.claim_name = claim_name

    def to_dict(self):
        return OrderedDict(
            {
                "name": self.name,
                "persistentVolumeClaim": {"claimName": self.claim_name},
            }
        )


class VolumeMount(object):
    def __init__(self, name, mount_path):
        self.name = name
        self.mount_path = mount_path

    def to_dict(self):
        return OrderedDict({"name": self.name, "mountPath": self.mount_path})
