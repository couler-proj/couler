import os

import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter
from couler.core.templates.volume import VolumeMount, Volume

#couler.add_volume(Volume("apppath", "mnist"))

mount = VolumeMount("apppath", "/data/")
command = ["ls", mount.mount_path]

couler.run_container(
        image="alpine:3.12.0", command=command, volume_mounts=[mount]
    )

submitter = ArgoSubmitter(namespace="testagent")
couler.run(submitter=submitter)