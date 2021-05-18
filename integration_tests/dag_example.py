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


def job(name):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[name],
        step_name=name,
    )


def exit_handler_succeeded():
    return couler.run_container(
        image="alpine:3.6",
        command=["sh", "-c", 'echo "succeeded"'],
        step_name="success-exit",
    )


def exit_handler_failed():
    return couler.run_container(
        image="alpine:3.6",
        command=["sh", "-c", 'echo "failed"'],
        step_name="failure-exit",
    )


def random_code():
    import random

    res = "heads" if random.randint(0, 1) == 0 else "tails"
    print(res)


def conditional_parent():
    return couler.run_script(
        image="python:3.6", source=random_code, step_name="condition-parent"
    )


def conditional_child():
    return couler.run_container(
        image="python:3.6",
        command=["bash", "-c", 'echo "child is triggered based on condition"'],
        step_name="condition-child",
    )


#     A
#    / \
#   B   C
#  /
# D
def linear():
    couler.set_dependencies(lambda: job(name="A"), dependencies=None)
    couler.set_dependencies(lambda: job(name="B"), dependencies=["A"])
    couler.set_dependencies(lambda: job(name="C"), dependencies=["A"])
    couler.set_dependencies(lambda: job(name="D"), dependencies=["B"])


#   A
#  / \
# B   C
#  \ /
#   D
def diamond():
    couler.dag(
        [
            [lambda: job(name="A")],
            [lambda: job(name="A"), lambda: job(name="B")],  # A -> B
            [lambda: job(name="A"), lambda: job(name="C")],  # A -> C
            [lambda: job(name="B"), lambda: job(name="D")],  # B -> D
            [lambda: job(name="C"), lambda: job(name="D")],  # C -> D
        ]
    )


if __name__ == "__main__":
    for impl_type in [_SubmitterImplTypes.GO, _SubmitterImplTypes.PYTHON]:
        os.environ[_SUBMITTER_IMPL_ENV_VAR_KEY] = impl_type
        print(
            "Submitting DAG example workflow via %s implementation" % impl_type
        )
        couler.config_workflow(
            name="dag-%s" % impl_type.lower(),
            timeout=3600,
            time_to_clean=3600 * 1.5,
        )

        # 1) Add a linear DAG.
        linear()
        # 2) Add another step that depends on D and flips a coin.
        # 3) If the result is "heads", another child step is also
        # added to the entire workflow.
        couler.set_dependencies(
            lambda: couler.when(
                couler.equal(conditional_parent(), "heads"),
                lambda: conditional_child(),
            ),
            dependencies=["D"],
        )
        # 4) Add an exit handler that runs when the workflow succeeds.
        couler.set_exit_handler(
            couler.WFStatus.Succeeded, exit_handler_succeeded
        )
        # 5) Add an exit handler that runs when the workflow failed.
        couler.set_exit_handler(couler.WFStatus.Failed, exit_handler_failed)
        submitter = ArgoSubmitter(namespace="argo")
        couler.run(submitter=submitter)
