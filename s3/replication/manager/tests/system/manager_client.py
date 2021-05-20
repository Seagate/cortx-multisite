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
import os
import sys
import yaml
from s3replicationcommon.log import setup_logger


async def main():
    """main function

    Main function calls REST apis

    """
    host = '127.0.0.1'
    port = '8080'

    # Setup logging and get logger
    log_config_file = os.path.join(os.path.dirname(__file__),
                                   'config', 'logger_config.yaml')

    print("Using log config {}".format(log_config_file))
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        print("Failed to configure logging.\n")
        sys.exit(-1)

    # Create parser object
    parser = argparse.ArgumentParser(
        description='''Replication manager help''')

    # Adding arguments
    parser.add_argument(
        '--configfile',
        type=str,
        metavar='path',
        help='Path to replication manager configuration file(format: yaml)')
    parser.add_argument(
        '--job',
        type=str,
        metavar='job',
        default='testjobid',
        help='job id')
    parser.add_argument(
        '--subscriber',
        type=str,
        metavar='subscriber',
        default='testsubscriberid',
        help='subscriber id')
    parser.add_argument(
        '--prefetch_count',
        type=str,
        metavar='prefetch_count',
        default=2,
        help='prefetch count')

    # Parsing arguments
    args = parser.parse_args()
    job = args.job
    subscriber = str(args.subscriber)
    prefetch_count = args.prefetch_count

    # Read input config file and get host, port
    if args.configfile is not None:
        with open(args.configfile, 'r') as file_config:
            config = yaml.safe_load(file_config)
            host = config['manager'].get('host')
            port = str(config['manager'].get('port'))

    url = 'http://' + host + ':' + port

    # Start client session
    async with aiohttp.ClientSession() as session:

        # Add subscriber
        async with session.post(
                url + '/subscribers',
                json={'id': subscriber, 'foo': 'bar'}) as response:
            LOG.info('POST subscriber Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Get subscriber list
        async with session.get(url + '/subscribers') as response:
            LOG.info('GET subscriber list Status: {}'.format(response.status))
            html = await response.json()
            LOG.info('Body: {}'.format(html))

        # Add Job
        async with session.post(
                url + '/jobs', json={"Object-Name": "foo"}) as response:
            logger.info('POST job Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))

        # Get jobs in progress
        async with session.get(
                url + '/jobs', params={"inprogress": "true"}) as response:
            logger.info('GET job Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))

        # Get jobs list
        async with session.get(url + '/jobs')as response:
            logger.info('GET job list Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))

        # Prefetch jobs
        async with session.get(
                url + '/jobs',
                params={
                    "prefetch": int(prefetch_count),
                    "subscriber_id": subscriber}) as response:
            logger.info('GET prefetch-job Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))

        # Get total job count
        async with session.get(
                url + '/jobs', params={"count": "true"}) as response:
            logger.info('GET count Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))

        # Update job's attributes
        async with session.put(
                url + '/jobs/' + job, json={"K2": "V2"}) as response:
            logger.info('PUT job Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))

        # Remove subscriber
        async with session.delete(
                url + '/subscribers/' + subscriber)as response:
            LOG.info('DELETE subscriber Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
