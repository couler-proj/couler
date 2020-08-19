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

import io
import os

from setuptools import find_packages, setup

with open("requirements.txt") as f:
    required_deps = f.read().splitlines()

extras = {}
with open("requirements-dev.txt") as f:
    extras["develop"] = f.read().splitlines()

version = {}  # type: dict
with io.open(os.path.join("couler", "_version.py")) as fp:
    exec(fp.read(), version)

setup(
    name="couler",
    description="Couler Python SDK/CLI",
    long_description="Couler Python SDK/CLI",
    version=version["__version__"],
    include_package_data=True,
    install_requires=required_deps,
    extras_require=extras,
    python_requires=">=3.6",
    packages=find_packages(exclude=["*test*", "step_zoo"]),
    package_data={"": ["requirements.txt"]},
)
