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

import aiohttp
import asyncio
import fileinput
import os
import re
import sys
import urllib
from os.path import abspath, join, dirname
from s3replicationcommon.aws_v4_signer import AWSV4Signer

# Import config module from '../tests/system'
sys.path.append(abspath(join(dirname(__file__),'..','tests', 'system')))
from config import Config

async def main():
    async with aiohttp.ClientSession() as session:
        config = Config()

        bucket_name = config.source_bucket_name
        object_name = config.object_name_prefix #+ "test"
        tag_name = config.object_tag_name
        tag_value = config.object_tag_value

        request_uri = AWSV4Signer.fmt_s3_request_uri(bucket_name, object_name)
        query_params = urllib.parse.urlencode({'tagging': ''})
        body = ""
        # Create temporary tagset file.
        os.system('cp ./tests/system/config/object_tagset.xml tagset.xml')
        matches = ['_TAG_KEY_', '_TAG_VALUE_']

        # Read tagset and make replacements based on config options.
        with fileinput.FileInput('tagset.xml', inplace=True) as file:
            # Read each line and match the pattern and do replacement.
            for line in file:
                if all(x in line for x in matches):
                    line = re.sub('(_TAG_KEY_)', tag_name, line)
                    line = re.sub('(_TAG_VALUE_)', tag_value, line)
                    print(line)
                else:
                    print(line, end='')
        os.system('cat tagset.xml')

        # open a file and read the tagset
        file = os.open('tagset.xml',os.O_RDONLY)
        tagset = os.read(file, os.path.getsize(file))

        headers = AWSV4Signer(
            config.endpoint,
            config.s3_service_name,
            config.s3_region,
            config.access_key,
            config.secret_key).prepare_signed_header(
            'PUT',
            request_uri,
            query_params,
            body)

        if (headers['Authorization'] is None):
            print("Failed to generate v4 signature")
            sys.exit(-1)

        print('PUT on {}'.format(config.endpoint + request_uri))

        async with session.put(config.endpoint + request_uri,
            data=tagset, params=query_params, headers=headers) as resp:
            http_status = resp.status
            print("Response of PUT request {} ".format(resp))

        if http_status == 200:
            print("HTTP status {} OK!".format(http_status))
        else:
            print("ERROR : BAD RESPONSE! status = {}".format(http_status))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
