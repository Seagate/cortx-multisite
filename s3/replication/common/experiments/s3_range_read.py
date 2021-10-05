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

from config import Config
import aiohttp
import asyncio
import sys
from os.path import abspath, join, dirname
from s3replicationcommon.aws_v4_signer import AWSV4Signer

# Import config module from '../tests/system'
sys.path.append(abspath(join(dirname(__file__), '..', 'tests', 'system')))


async def main():
    async with aiohttp.ClientSession() as session:

        config = Config()

        # Ensure bucket and object exists before test.
        bucket_name = config.source_bucket_name
        object_name = config.object_name_prefix + "test"

        # Get object range from config
        obj_range = config.object_range

        request_uri = AWSV4Signer.fmt_s3_request_uri(bucket_name, object_name)
        query_params = ""
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
            body,
            obj_range)

        if (headers['Authorization'] is None):
            print("Failed to generate v4 signature")
            sys.exit(-1)

        print('GET on {}'.format(config.endpoint + request_uri))
        async with session.get(config.endpoint + request_uri,
                               headers=headers) as resp:
            http_status = resp.status

        if http_status == 206:
            print("HTTP status {} OK!".format(http_status))
        else:
            print("ERROR : BAD RESPONSE! status = {}".format(http_status))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
