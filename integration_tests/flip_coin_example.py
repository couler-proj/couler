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


def random_code():
    import random

    res = "heads" if random.randint(0, 1) == 0 else "tails"
    print(res)


def flip_coin():
    return couler.run_script(image="python:alpine3.6", source=random_code)


def heads():
    return couler.run_container(
        image="alpine:3.6", command=["sh", "-c", 'echo "it was heads"']
    )


def tails():
    return couler.run_container(
        image="alpine:3.6", command=["sh", "-c", 'echo "it was tails"']
    )


if __name__ == "__main__":
    for impl_type in [_SubmitterImplTypes.GO, _SubmitterImplTypes.PYTHON]:
        os.environ[_SUBMITTER_IMPL_ENV_VAR_KEY] = impl_type
        print("Submitting workflow via %s implementation" % impl_type)
        couler.config_workflow(timeout=3600, time_to_clean=3600 * 1.5)
        result = flip_coin()
        couler.when(couler.equal(result, "heads"), lambda: heads())
        couler.when(couler.equal(result, "tails"), lambda: tails())

        submitter = ArgoSubmitter(namespace="argo")
        couler.run(submitter=submitter)
        print("Workflow submitted for flip coin example")
