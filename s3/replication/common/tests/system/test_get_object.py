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

import asyncio
import os
import sys
from config import Config
from s3replicationcommon.log import setup_logger
from s3replicationcommon.s3_site import S3Site
from s3replicationcommon.s3_session import S3Session
from s3replicationcommon.s3_get_object import S3AsyncGetObject


async def main():

    config = Config()

    # Setup logging and get logger
    log_config_file = os.path.join(os.path.dirname(__file__),
                                   'config', 'logger_config.yaml')

    print("Using log config {}".format(log_config_file))
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        print("Failed to configure logging.\n")
        sys.exit(-1)

    s3_site = S3Site(config.endpoint, config.s3_service_name, config.s3_region)

    session = S3Session(logger, s3_site, config.access_key, config.secret_key)

    # Generate bucket names
    bucket_name = config.source_bucket_name

    # Generate object names
    object_name = str(config.object_name_prefix)
    object_size = config.object_size
    range_read_offset = config.range_read_offset
    range_read_length = config.range_read_length
    request_id = "dummy-request-id"

    object_reader = S3AsyncGetObject(session, request_id,
                                     bucket_name, object_name,
                                     object_size, range_read_offset,
                                     range_read_length)

    reader_generator = object_reader.fetch(object_size)
    async for _ in reader_generator:
        pass

    content_length = object_reader.get_content_length()

    if range_read_length >= 0:
        # Validate if content length matches to total object range
        if object_reader.get_total_object_range() == content_length:
            logger.info("Content-Length matched!")
            logger.info("S3AsyncGetObjectRangeRead test passed!")
        else:
            logger.error("Error : size mismatched")
            logger.info("S3AsyncGetObjectRangeRead test failed!")
    else:
        # Validate if content length matches to object size in config
        if object_size == content_length:
            logger.info("Content-Length matched!")
            logger.info("S3AsyncGetObject test passed!")
        else:
            logger.error("Error : size mismatched")
            logger.info("S3AsyncGetObject test failed!")

    await session.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
