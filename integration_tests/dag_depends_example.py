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

import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter

if __name__ == "__main__":
    couler.config_workflow(timeout=3600, time_to_clean=3600 * 1.5)

    def pass_step(name):
        return couler.run_container(
            image="reg.docker.alibaba-inc.com/couler/python:3.6",
            command=["bash", "-c", "exit 0"],
            step_name=name,
        )

    def fail_step(name):
        return couler.run_container(
            image="reg.docker.alibaba-inc.com/couler/python:3.6",
            command=["bash", "-c", "exit 1"],
            step_name=name,
        )

    couler.set_dependencies(lambda: pass_step("A"), dependencies=None)
    couler.set_dependencies(lambda: pass_step("B"), dependencies="A")
    couler.set_dependencies(lambda: fail_step("C"), dependencies="A")
    couler.set_dependencies(
        lambda: pass_step("should-execute-1"),
        dependencies="A && (C.Succeeded || C.Failed)",
    )
    couler.set_dependencies(
        lambda: pass_step("should-execute-2"), dependencies="B || C"
    )
    couler.set_dependencies(
        lambda: pass_step("should-not-execute"), dependencies="B && C"
    )
    couler.set_dependencies(
        lambda: pass_step("should-execute-3"),
        dependencies="should-execute-2.Succeeded || should-not-execute",
    )

    submitter = ArgoSubmitter(namespace="argo")
    wf = couler.run(submitter=submitter)
    wf_name = wf["metadata"]["name"]
    print("Workflow %s has been submitted for DAG depends example" % wf_name)
