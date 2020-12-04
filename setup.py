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

import distutils.cmd
import io
import os

from setuptools import find_packages, setup


class ProtocCommand(distutils.cmd.Command):
    description = "run protoc to compile protobuf files"
    user_options = []

    def initialize_options(self):
        """Set default values for options."""
        pass

    def finalize_options(self):
        """Post-process options."""
        pass

    def run(self):
        os.system("protoc --python_out=couler proto/couler.proto")
        os.system("touch couler/proto/__init__.py")
        self.announce(
            "proto file generated under couler/proto.",
            level=distutils.log.INFO,
        )


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
    description="Unified Interface for Constructing and Managing Workflows",
    long_description="Unified Interface for"
    " Constructing and Managing Workflows",
    version=version["__version__"],
    include_package_data=True,
    install_requires=required_deps,
    extras_require=extras,
    python_requires=">=3.6",
    packages=find_packages(exclude=["*test*"]),
    package_data={"": ["requirements.txt"]},
    cmdclass={"proto": ProtocCommand},
)
