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

import aiohttp
import asyncio
import argparse
import yaml
from s3replicationcommon.log import setup_logging

async def main():
    """"main function

    Main function for calling various REST requests.

    """
    host = '127.0.0.1'
    port = '8081'

    # Setup logging and get logger
    LOG = setup_logging('replicator_client')

    # Create parser object
    parser = argparse.ArgumentParser(description='''Replicator server help''')

    # Adding an arguments
    parser.add_argument('--configfile', type=str, metavar='path', help='Path to replication manager configuration file(format: yaml)')
    parser.add_argument('job', type=str, metavar='job', help='job id')

    # Parsing arguments
    args = parser.parse_args()
    job = args.job

    # Read input config file and get host, port
    if args.configfile is not None:
        with open(args.configfile, 'r') as file_config:
            config = yaml.safe_load(file_config)
            host = config['replicator'].get('host')
            port = str(config['replicator'].get('port'))

    # URL for non-secure http endpoint
    url = 'http://'+host+':'+port

    # Start client session
    async with aiohttp.ClientSession() as session:

        # Add job and attributes
        async with session.put(
        url+'/jobs', json={"job2": "bar"}) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get job attributes
        async with session.get(
        url+'/jobs/' + job) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get inprogress list
        async with session.get(url+'/jobs')as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Abort job with given job_id
        async with session.post(url+'/jobs/' + job) as response:
            LOG.info('Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
