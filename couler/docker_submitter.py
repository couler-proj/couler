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

import logging

import docker


class DockerSubmitter(object):
    @staticmethod
    def run_docker_container(image, command):
        client = docker.from_env()
        container = client.containers.run(image, command, detach=True)
        # Streaming the logs
        for line in container.logs(stream=True):
            logging.info(line.strip())
