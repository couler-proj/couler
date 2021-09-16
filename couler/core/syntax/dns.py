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

from couler.core import states
from couler.core.templates.dns import DnsConfig


def set_dns(dns_policy: str, dns_config: DnsConfig):
    """
    Set dns policy and config to the workflow.
    https://argoproj.github.io/argo-workflows/fields/#poddnsconfig
    """
    states.workflow.set_dns(dns_policy, dns_config)
