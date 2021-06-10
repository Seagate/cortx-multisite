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
import pytest
import json
import uuid

from s3replicationcommon.log import setup_logger
from s3replicationcommon.templates import subscribe_payload_template


@pytest.fixture
def event_loop():
    """Fixture for async operations."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def logger():
    """Setup logger for tests."""
    # Setup logging and get logger
    log_config_file = os.path.join(
        os.path.dirname(__file__), 'config', 'logger_config.yaml')
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        sys.exit(-1)
    return logger


@pytest.fixture
def test_config(logger):
    """Fixture for Replication manager host, port configuration."""
    host = '127.0.0.1'
    port = '8080'

    # Replication manager Connection config
    config_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'src', 'config', 'config.yaml')
    logger.debug("Using Replication manager config from {}".
                 format(config_path))

    with open(config_path, 'r') as file_config:
        config = yaml.safe_load(file_config)
        host = config['manager'].get('host')
        port = str(config['manager'].get('port'))

    # URL for non-secure http endpoint
    url = 'http://' + host + ':' + port

    return {'url': url}


@pytest.fixture()
def fdmi_job(logger):
    """fdmi job fixture to load fdmi record."""
    fdmi_job_record = None

    job_file = os.path.join(
        os.path.dirname(__file__), 'data', 'fdmi_test_job.json')
    logger.debug("Using fdmi record from {}".format(job_file))

    with open(job_file, 'r') as file_config:
        fdmi_job_record = json.load(file_config)

    return fdmi_job_record


@pytest.fixture()
def subscriber_record(logger):
    """Prepare subscriber payload for tests."""
    subscriber_payload = subscribe_payload_template()

    subscriber_payload["id"] = str(uuid.uuid4())
    subscriber_payload["endpoint"] = "http://localhost:8081/"
    subscriber_payload["prefetch_count"] = "5"

    return subscriber_payload


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case_name, expected_http_status",
    [('valid_job', 201),
     ('empty_job', 500)])
async def test_post_job(logger, test_config, fdmi_job,
                        test_case_name, expected_http_status):
    """Post job tests."""
    test_data = {'valid_job': fdmi_job, 'empty_job': {}}

    test_payload = test_data[test_case_name]

    async with aiohttp.ClientSession() as session:
        # Add job and attributes
        async with session.post(test_config['url'] + '/jobs',
                                json=test_payload) as response:

            response_body = await response.json()
            logger.debug('HTTP Response: Status: {}, Body: {}'.format(
                response.status, response_body))

            assert expected_http_status == response.status, \
                "ERROR : Received http status : " + str(response.status) + \
                "Expected http status :" + str(expected_http_status)

            logger.info(
                'POST successful: http status: {}'.format(response.status))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case_name, expected_http_status",
    [('valid_payload', 201),
     ('empty_payload', 500)])
async def test_post_subscriber(logger, test_config, subscriber_record,
                               test_case_name, expected_http_status):
    """Post job tests."""
    test_data = {'valid_payload': subscriber_record, 'empty_payload': {}}

    test_payload = test_data[test_case_name]

    async with aiohttp.ClientSession() as session:
        # Add subscriber
        async with session.post(test_config['url'] + '/subscribers',
                                json=test_payload) as response:

            response_body = await response.json()
            logger.debug('HTTP Response: Status: {}, Body: {}'.format(
                response.status, response_body))

            assert expected_http_status == response.status, \
                "ERROR : Received http status : " + str(response.status) + \
                "Expected http status :" + str(expected_http_status)

            logger.info(
                'POST successful: http status: {}'.format(response.status))
