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

import os

import couler.argo as couler
from couler.argo_submitter import (
    _SUBMITTER_IMPL_ENV_VAR_KEY,
    ArgoSubmitter,
    _SubmitterImplTypes,
)
from couler.core.templates.volume import VolumeMount

if __name__ == "__main__":
    for impl_type in [_SubmitterImplTypes.PYTHON]:
        os.environ[_SUBMITTER_IMPL_ENV_VAR_KEY] = impl_type
        print(
            "Submitting volume example workflow via %s implementation"
            % impl_type
        )
        couler.config_workflow(
            name="volume-%s" % impl_type.lower(),
            timeout=3600,
            time_to_clean=3600 * 1.5,
        )
        # 2) Add a container to the workflow.
        couler.run_container(
            image="debian:latest",
            command=["/bin/bash", "-c"],
            args=[
                ' vol_found=`mount | grep /tmp` && \
            if [[ -n $vol_found ]]; \
            then echo "Volume mounted and found"; \
            else exit -1; fi '
            ],
            volume_mounts=[VolumeMount("apppath", "/tmp")],
        )
        submitter = ArgoSubmitter(namespace="argo")
        couler.run(submitter=submitter)
