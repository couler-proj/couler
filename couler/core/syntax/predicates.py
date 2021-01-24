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


def _predicate(pre, post, condition):
    """Generates an Argo predicate.
    """
    dict_config = {}
    if callable(pre):
        dict_config["pre"] = pre()
    else:
        dict_config["pre"] = pre

    if callable(post):
        dict_config["post"] = post()
    else:
        dict_config["post"] = post

    # TODO: check the condition
    dict_config["condition"] = condition

    return dict_config


def equal(pre, post=None):
    if post is not None:
        return _predicate(pre, post, "==")
    else:
        return _predicate(pre, None, "==")


def not_equal(pre, post=None):
    if post is not None:
        return _predicate(pre, post, "!=")
    else:
        return _predicate(pre, None, "!=")


def bigger(pre, post=None):
    if post is not None:
        return _predicate(pre, post, ">")
    else:
        return _predicate(pre, None, ">")


def smaller(pre, post=None):
    if post is not None:
        return _predicate(pre, post, "<")
    else:
        return _predicate(pre, None, "<")


def bigger_equal(pre, post=None):
    if post is not None:
        return _predicate(pre, post, ">=")
    else:
        return _predicate(pre, None, ">=")


def smaller_equal(pre, post=None):
    if post is not None:
        return _predicate(pre, post, "<=")
    else:
        return _predicate(pre, None, "<=")
