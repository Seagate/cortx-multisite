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

# s3 replicator client
#
# This file contains replicator client
# with various REST requests.

import sys
import aiohttp
import asyncio
import logging
from s3replicationcommon.log import setup_logging

LOG = logging.getLogger('multisite')

async def main():
    """"main function

    Main function for calling various REST requests.

    """
    setup_logging()

    async with aiohttp.ClientSession() as session:

        # Get inprogress list
        async with session.get('http://127.0.0.1:8080/jobs')as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get job attributes
        async with session.get(
        'http://0.0.0.0:8080/jobs/' + sys.argv[1]) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Add job and attributes
        async with session.put(
        'http://0.0.0.0:8080/jobs', json={"job2": "bar"}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get job attributes
        async with session.get(
        'http://0.0.0.0:8080/jobs/job2') as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Abort job with given job_id
        async with session.post(
        'http://0.0.0.0:8080/jobs/' + sys.argv[1]) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
