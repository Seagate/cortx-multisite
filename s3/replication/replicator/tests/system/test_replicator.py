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

# s3 replicator test file
#
# This file contains replicator tests
# with various REST requests.

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
test_job = {}

# String to save job_id of posted job
job_uuid = ''


@pytest.fixture()
def jobfile(pytestconfig):
    return pytestconfig.getoption("jobfile")


@pytest.fixture()
def configfile(pytestconfig):
    return pytestconfig.getoption("configfile")


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def setup_config(configfile, jobfile):
    global logger

    host = '127.0.0.1'
    port = '8081'

    # Setup logging and get logger
    log_config_file = os.path.join(os.path.dirname(__file__),
                                   'config', 'logger_config.yaml')
    print("Using log config {}".format(log_config_file))
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        print("Failed to configure logging.\n")
        sys.exit(-1)

    with open(configfile, 'r') as file_config:
        config = yaml.safe_load(file_config)
        host = config['replicator'].get('host')
        port = str(config['replicator'].get('port'))

    # URL for non-secure http endpoint
    url = 'http://' + host + ':' + port

    with open(jobfile, 'r') as file_config:
        test_job = json.load(file_config)

    return [url, test_job]


@pytest.mark.asyncio
async def test_post_job(setup_config):
    global job_uuid

    async with aiohttp.ClientSession() as session:

        # Add job and attributes
        async with session.post(
                setup_config[0] + '/jobs', json=setup_config[1]) as response:
            logger.info('POST jobs Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))
            assert 201 == response.status, "ERROR : Bad response  : " + \
                str(response.status)
            job_uuid = html['job']['job_id']
            logger.info('job_uuid: {}'.format(job_uuid))


@pytest.mark.asyncio
async def test_get_job(setup_config):

    # Start client session
    async with aiohttp.ClientSession() as session:

        # Get job attributes
        async with session.get(
                setup_config[0] + '/jobs/' + job_uuid) as response:
            logger.info('GET jobs Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))
            assert 200 == response.status, "ERROR : Bad response : " + \
                str(response.status)


@pytest.mark.asyncio
async def test_get_list(setup_config):

    # Start client session
    async with aiohttp.ClientSession() as session:

        # Get inprogress list
        async with session.get(setup_config[0] + '/jobs') as response:
            logger.info('List jobs Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))
            assert 200 == response.status, "ERROR : Bad response : " + \
                str(response.status)


@pytest.mark.asyncio
async def test_abort_job(setup_config):

    # Start client session
    async with aiohttp.ClientSession() as session:

        # Abort job with given job_id
        async with session.delete(
                setup_config[0] + '/jobs/' + job_uuid) as response:
            logger.info('Abort job Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))
            assert 204 == response.status, "ERROR : Bad response : " + \
                str(response.status)
