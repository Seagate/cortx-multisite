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

from fixtures.subscribe import subscriber_record  # noqa: F401;


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case_name, expected_http_status",
    [('valid_payload', 201),
     ('empty_payload', 500)])
async def test_post_subscriber(logger, test_config,
                               subscriber_record,  # noqa: F811;
                               test_case_name, expected_http_status):
    """Post job tests."""
    test_data = {'valid_payload': subscriber_record, 'empty_payload': {}}

    test_payload = test_data[test_case_name]

    async with aiohttp.ClientSession() as session:
        # Add subscriber
        async with session.post(test_config['url'] + '/subscribers',
                                json=test_payload) as response:

            if test_case_name == 'valid_payload':
                response_body = await response.json()
                logger.debug('HTTP Response: Status: {}, Body: {}'.format(
                    response.status, response_body))

            assert expected_http_status == response.status, \
                "ERROR : Received http status : " + str(response.status) + \
                "Expected http status :" + str(expected_http_status)

            logger.info(
                'POST successful: http status: {}'.format(response.status))
