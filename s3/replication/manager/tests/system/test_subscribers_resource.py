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

import aiohttp
import pytest


# Global subscriber id to perform validations across test cases.
global_valid_subscriber_id = ""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case_name, expected_http_status",
    [('valid_payload', 201),
     ('empty_payload', 500)])
async def test_post_subscriber(logger, test_config,
                               subscriber_record,  # noqa: F811;
                               test_case_name, expected_http_status):
    """Post subscriber tests."""
    test_data = {'valid_payload': subscriber_record, 'empty_payload': {}}

    test_payload = test_data[test_case_name]

    async with aiohttp.ClientSession() as session:
        # Add subscriber
        async with session.post(test_config['url'] + '/subscribers',
                                json=test_payload) as response:
            logger.debug('HTTP Response: Status: {}'.format(response.status))
            if test_case_name == 'valid_payload':
                response_body = await response.json()
                logger.debug('HTTP Response: Body: {}'.format(response_body))
                global global_valid_subscriber_id
                global_valid_subscriber_id = response_body["id"]

            assert expected_http_status == response.status, \
                "ERROR : Received http status : " + str(response.status) + \
                "Expected http status :" + str(expected_http_status)

            logger.info(
                'POST successful: http status: {}'.format(response.status))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case_name, expected_http_status",
    [('valid_subscriber', 200),
     ('missing_subscriber', 404)])
async def test_get_subscriber(logger, test_config,
                              subscriber_record,  # noqa: F811;
                              test_case_name, expected_http_status):
    """GET specific subscriber tests."""
    if test_case_name == "valid_subscriber":
        global global_valid_subscriber_id
        subscriber_id = global_valid_subscriber_id
    elif test_case_name == "missing_subscriber":
        subscriber_id = "invalid-subscriber-id"
    else:
        assert False, "Invalid test case."

    async with aiohttp.ClientSession() as session:
        # Add subscriber and attributes
        async with session.get(test_config['url'] + '/subscribers/' +
                               subscriber_id) as response:
            logger.debug('HTTP Response: Status: {}'.format(response.status))

            if test_case_name == 'valid_subscriber':
                response_body = await response.json()
                logger.debug('HTTP Response Body: {}'.format(response_body))

            assert expected_http_status == response.status, \
                "ERROR : Received http status : " + str(response.status) + \
                "Expected http status :" + str(expected_http_status)

            logger.info(
                'GET subscriber successful: http status: {}'.format(
                    response.status))


@pytest.mark.asyncio
async def test_get_subscribers(logger, test_config):
    """GET subscribers list, expected entries added in post."""
    expected_http_status = 200
    expected_count = 1

    global global_valid_subscriber_id
    subscriber_id = global_valid_subscriber_id

    async with aiohttp.ClientSession() as session:
        # Get subscribers list.
        async with session.get(
                test_config['url'] + '/subscribers') as response:

            logger.debug('HTTP Response: Status: {}'.format(response.status))

            subscribers_list = await response.json()
            logger.debug('HTTP Response Body: {}'.format(subscribers_list))

            assert expected_http_status == response.status, \
                "ERROR : Received http status : " + str(response.status) + \
                "Expected http status :" + str(expected_http_status)

            assert len(subscribers_list) == expected_count, \
                "ERROR : Invalid expected subscribers count." + \
                "Received {} subscribers.\nExpected {} subscribers".format(
                    len(subscribers_list), expected_count)

            # Access the first subscriber.
            subscriber = next(iter(subscribers_list.items()))[1]
            assert subscriber_id == subscriber["id"], \
                "ERROR : Expected subscriber is missing." + \
                "subscriber_id = {}".format(
                    subscriber_id
            )

            logger.info(
                'GET subscribers successful: http status: {}'.format(
                    response.status))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case_name, expected_http_status",
    [('valid_subscriber', 204),
     ('missing_subscriber', 404)])
async def test_delete_subscriber(logger, test_config,
                                 subscriber_record,  # noqa: F811;
                                 test_case_name, expected_http_status):
    """DELETE specific subscriber tests."""
    if test_case_name == "valid_subscriber":
        global global_valid_subscriber_id
        subscriber_id = global_valid_subscriber_id
    elif test_case_name == "missing_subscriber":
        subscriber_id = "invalid-subscriber-id"
    else:
        assert False, "Invalid test case."

    async with aiohttp.ClientSession() as session:
        # Add subscriber and attributes
        async with session.delete(test_config['url'] + '/subscribers/' +
                                  subscriber_id) as response:
            logger.debug('HTTP Response: Status: {}'.format(response.status))

            assert expected_http_status == response.status, \
                "ERROR : Received http status : " + str(response.status) + \
                "Expected http status :" + str(expected_http_status)

            logger.info(
                'DELETE subscriber successful: http status: {}'.format(
                    response.status))


@pytest.mark.asyncio
async def test_get_subscribers_empty(logger, test_config):
    """GET subscribers list, expected empty after delete."""
    expected_http_status = 200
    expected_count = 0

    async with aiohttp.ClientSession() as session:
        # Get subscribers list.
        async with session.get(
                test_config['url'] + '/subscribers') as response:

            logger.debug('HTTP Response: Status: {}'.format(response.status))

            subscribers_list = await response.json()
            logger.debug('HTTP Response Body: {}'.format(subscribers_list))

            assert expected_http_status == response.status, \
                "ERROR : Received http status : " + str(response.status) + \
                "Expected http status :" + str(expected_http_status)

            assert len(subscribers_list) == expected_count, \
                "ERROR : Invalid expected subscribers count." + \
                "Received {} subscribers.\nExpected {} subscribers".format(
                    len(subscribers_list), expected_count)

            logger.info(
                'GET subscribers successful: http status: {}'.format(
                    response.status))
