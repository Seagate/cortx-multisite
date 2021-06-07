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

# s3 replication manager pytest
#
# This file contains replication manager's tests with
# various REST requests.

import aiohttp
import asyncio
import os
import sys
import yaml
from s3replicationcommon.log import setup_logger
import pytest
import json

logger = None

# Load the test job record.
fdmi_job_record = {}
empty_record = {}


@pytest.fixture()
def fdmi_job():
    """fdmi job fixture to read and load fdmi record."""

    global fdmi_job_record

    job_file = os.path.join(
        os.path.dirname(__file__), 'data', 'fdmi_test_job.json')
    with open(job_file, 'r') as file_config:
        fdmi_job_record = json.load(file_config)
    return fdmi_job_record


@pytest.fixture
def event_loop():
    """Fixture for async operations."""

    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config(fdmi_job):
    """Fixture for host, port configuration."""

    global logger

    host = '127.0.0.1'
    port = '8080'

    # Setup logging and get logger
    log_config_file = os.path.join(
        os.path.dirname(__file__), 'config', 'logger_config.yaml')
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        sys.exit(-1)

    # Connection config
    config = os.path.join(
        os.path.dirname(__file__), '..', '..', 'src', 'config', 'config.yaml')

    with open(config, 'r') as file_config:
        config = yaml.safe_load(file_config)
        host = config['manager'].get('host')
        port = str(config['manager'].get('port'))

    # URL for non-secure http endpoint
    url = 'http://' + host + ':' + port

    return {'url': url}


@pytest.mark.asyncio
@pytest.mark.parametrize('test_input_param', ['valid_job', 'empty_job'])
async def test_post_job(test_config, test_input_param):
    """Pytest for post job test."""
    input_test = {'valid_job': fdmi_job_record, 'empty_job': {}}

    test_input = input_test[test_input_param]

    async with aiohttp.ClientSession() as session:

        # Add job and attributes
        async with session.post(
                test_config['url'] + '/jobs',
                json=test_input) as response:
            logger.info(
                'POST job returned http Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))
            if test_input_param == 'valid_job':
                assert 201 == response.status, "ERROR : Bad response  : " + \
                    str(response.status)
                logger.info('POST job successful.')
            elif test_input_param == 'empty_job':
                assert 500 == response.status, "ERROR : Bad response  : " + \
                    str(response.status)
                logger.info('POST job fail. Empty json')
