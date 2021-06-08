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
import asyncio
import argparse
import os
import sys
import yaml
import json
from s3replicationcommon.log import setup_logger


async def main():
    """"Main function for calling various REST requests."""
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

    # Create parser object
    parser = argparse.ArgumentParser(description='''Replicator server help''')

    # Adding an arguments
    parser.add_argument(
        '--configfile',
        type=str,
        metavar='path',
        help='Path to replication manager configuration file(format: yaml)')

    parser.add_argument(
        '--jobfile',
        type=str,
        metavar='path',
        help='Test job record')

    # Parsing arguments
    args = parser.parse_args()

    # Read input config file and get host, port
    if args.configfile is None:
        args.configfile = os.path.join(os.path.dirname(__file__),
                                       "..", "..", "src", 'config',
                                       'config.yaml')
    with open(args.configfile, 'r') as file_config:
        config = yaml.safe_load(file_config)
        host = config['replicator'].get('host')
        port = str(config['replicator'].get('port'))

    # URL for non-secure http endpoint
    url = 'http://' + host + ':' + port

    # Load the test job record.
    test_job = {}
    if args.jobfile is None:
        args.jobfile = os.path.join(os.path.dirname(__file__),
                                    'data', 'test_job.json')
    with open(args.jobfile, 'r') as file_config:
        test_job = json.load(file_config)

    # Start client session
    async with aiohttp.ClientSession() as session:

        # Post the replication job
        async with session.post(
                url + '/jobs', json=test_job) as response:
            logger.info('POST jobs Status: {}'.format(response.status))
            html = await response.json()
            logger.info('Body: {}'.format(html))

        # XXX Monitor the status - check if replication is complete.


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
