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

#
# Test file to get bucket's replication policy.
#

import aiohttp
import asyncio
import sys
import urllib
from config import Config
from s3replicationcommon.aws_v4_signer import AWSV4Signer

# Import config module from '../tests/system'
sys.path.append(abspath(join(dirname(__file__),'..','tests', 'system')))
from config import Config

async def main():
    async with aiohttp.ClientSession() as session:

        config = Config()

        # Ensure bucket is exists before test.
        bucket_name = config.source_bucket_name
        request_uri = AWSV4Signer.fmt_s3_request_uri(bucket_name)
        query_params = urllib.parse.urlencode({'replication': None})
        body = ""

        headers = AWSV4Signer(
            config.endpoint,
            config.s3_service_name,
            config.s3_region,
            config.access_key,
            config.secret_key).prepare_signed_header(
            'GET',
            request_uri,
            query_params,
            body)

        if (headers['Authorization'] is None):
            print("Failed to generate v4 signature")
            sys.exit(-1)

        # Request url
        url = config.endpoint + request_uri

        print('GET on {}'.format(url))
        async with session.get(
                url, params=query_params, headers=headers) as resp:
            print("Response url {}".format((resp.url)))
            print("Received reponse {}".format((resp)))

            total_received = 0
            while True:
                chunk = await resp.content.read(1024)
                if not chunk:
                    break
                total_received += len(chunk)
                print("Received chunk {}".format(chunk))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
