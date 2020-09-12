import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter


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


def job_a(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="A",
    )


def job_b(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="B",
    )


def job_c(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="C",
    )


def job_d(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="D",
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


#  A
# / \
# B  C
# /
# D
def linear():
    couler.set_dependencies(lambda: job_a(message="A"), dependencies=None)
    couler.set_dependencies(lambda: job_b(message="B"), dependencies=["A"])
    couler.set_dependencies(lambda: job_c(message="C"), dependencies=["A"])
    couler.set_dependencies(lambda: job_d(message="D"), dependencies=["B"])


#  A
# / \
# B  C
# \  /
#  D
def diamond():
    couler.dag(
        [
            [lambda: job_a(message="A")],
            [lambda: job_a(message="A"), lambda: job_b(message="B")],  # A -> B
            [lambda: job_a(message="A"), lambda: job_c(message="C")],  # A -> C
            [lambda: job_b(message="B"), lambda: job_d(message="D")],  # B -> D
            [lambda: job_b(message="C"), lambda: job_d(message="D")],  # C -> D
        ]
    )


if __name__ == "__main__":
    couler.config_workflow(timeout=3600, time_to_clean=3600 * 1.5)

    linear()
    couler.set_exit_handler(couler.WFStatus.Succeeded, exit_handler_succeeded)
    couler.set_exit_handler(couler.WFStatus.Failed, exit_handler_failed)

    submitter = ArgoSubmitter(namespace="argo")
    wf = couler.run(submitter=submitter)
    wf_name = wf["metadata"]["name"]
    print("Workflow %s has been submitted for DAG example" % wf_name)
