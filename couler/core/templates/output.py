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


class Output(object):
    def __init__(self, value, is_global=False):
        self.value = value
        self.is_global = is_global


class OutputEmpty(Output):
    def __init__(self, value, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)


class OutputParameter(Output):
    def __init__(self, value, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)


class OutputArtifact(Output):
    def __init__(self, value, path, artifact, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)
        self.path = path
        self.artifact = artifact


class OutputScript(Output):
    def __init__(self, value, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)


class OutputJob(Output):
    def __init__(self, value, job_name, job_id, job_obj=None, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)
        self.job_name = job_name
        self.job_id = job_id
        self.job_obj = job_obj
