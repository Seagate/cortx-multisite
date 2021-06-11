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

import json
import os
import pytest


@pytest.fixture()
def fdmi_job(logger):
    """fdmi job fixture to load fdmi record."""
    fdmi_job_record = None

    job_file = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'fdmi_test_job.json')
    logger.debug("Using fdmi record from {}".format(job_file))

    with open(job_file, 'r') as file_config:
        fdmi_job_record = json.load(file_config)

    return fdmi_job_record
