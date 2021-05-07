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

# s3 replication-manager client
#
# This file contains replication-manager client source
# which makes various REST api calls.
#

import aiohttp
import asyncio
import argparse
import yaml
from s3replicationcommon.log import setup_logging

async def main():
    """main function

    Main function calls REST apis

    """
    host = '127.0.0.1'
    port = '8080'

    # Setup logging and get logger
    LOG = setup_logging('manager_client')

    # Create parser object
    parser = argparse.ArgumentParser(description='''Replicator server help''')

    # Adding arguments
    parser.add_argument('--configfile', type=str, metavar='path', help='Path to replication manager configuration file(format: yaml)')
    parser.add_argument('job', type=str, metavar='job', help='job id')
    parser.add_argument('subscriber', type=str, metavar='subscriber', help='subscriber id')
    parser.add_argument('prefetch_count', type=str, metavar='prefetch_count', help='prefetch count')

    # Parsing arguments
    args = parser.parse_args()
    job = args.job
    subscriber = args.subscriber
    prefetch_count = args.prefetch_count

    # Read input config file and get host, port
    if args.configfile is not None:
        with open(args.configfile, 'r') as file_config:
            config = yaml.safe_load(file_config)
            host = config['manager'].get('host')
            port = str(config['manager'].get('port'))

    url = 'http://'+host+':'+port

    # Start client session
    async with aiohttp.ClientSession() as session:

        # Add Job
        async with session.post(url+'/jobs', json={job: {"K1": "V1"}}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get Jobs in Progress
        async with session.get(
            url+'/jobs', params={"inprogress": "true"}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get jobs list
        async with session.get(url+'/jobs')as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get subscriber list
        async with session.get(url+'/subscribers') as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Add subscriber
        async with session.post(url+'/subscribers', json={'sub_id': subscriber}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Prefetch jobs
        async with session.get(url+'/jobs', params={"prefetch": int(prefetch_count), "subscriber_id": subscriber}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get total job count
        async with session.get(url+'/jobs', params={"count": "true"}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Update Job's attributes
        async with session.put(url+'/jobs/' + job, json={"K2": "V2"}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
