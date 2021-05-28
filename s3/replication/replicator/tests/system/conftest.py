#!/usr/bin/env python3

#
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

# conftest.py

# This is a place for common fixture functions.
# Fixures defined here are accessible across
# multiple test files.

import os

default_jobfile = os.path.join(
    os.path.dirname(__file__),
    'data',
    'test_job.json')
default_configfile = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    'src',
    'config',
    'config.yaml')


def pytest_addoption(parser):

    parser.addoption("--jobfile", action="store", default=default_jobfile)

    parser.addoption(
        "--configfile",
        action="store",
        default=default_configfile)
