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

# s3 replicator-manager client
#
# This file contains replicator-manager client source
# which makes various REST api calls.
#
# Run as : python3 ./manager_client.py [job_id] [subscriber_id] [prefetch_cnt]
#

import sys
import aiohttp
import asyncio
import logging
from s3replicationcommon.log import setup_logging

LOG = logging.getLogger('multisite')

async def main():
    """main function

    Main function calls REST apis

    """
    setup_logging()

    async with aiohttp.ClientSession() as session:

        # Add Job
        async with session.post('http://127.0.0.1:8080/jobs', json={sys.argv[1]: {"K1": "V1"}}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get Jobs in Progress
        async with session.get(
            'http://127.0.0.1:8080/jobs', params={"inprogress": "true"}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get jobs list
        async with session.get('http://127.0.0.1:8080/jobs')as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get subscriber list
        async with session.get('http://127.0.0.1:8080/subscribers') as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Add subscriber
        async with session.post('http://127.0.0.1:8080/subscribers', json={'sub_id': sys.argv[2] }) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Prefetch jobs
        async with session.get('http://127.0.0.1:8080/jobs',params={"prefetch": int(sys.argv[3]), "subscriber_id": sys.argv[2]}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get total job count
        async with session.get('http://127.0.0.1:8080/jobs',params={"count": "true"}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Update Job's attributes
        async with session.put('http://127.0.0.1:8080/jobs/' + sys.argv[1], json={"K2": "V2"}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
