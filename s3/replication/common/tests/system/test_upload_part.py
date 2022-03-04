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

import asyncio
import os
import sys
from config import Config
from s3replicationcommon.log import setup_logger
from object_generator_multipart_upload import MultipartObjectDataGenerator
from s3replicationcommon.s3_upload_part import S3AsyncUploadPart
from s3replicationcommon.s3_site import S3Site
from s3replicationcommon.s3_session import S3Session


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

    # Generate object name
    object_name = str(config.object_name_prefix)
    bucket_name = config.source_bucket_name
    total_parts = config.total_parts
    request_id = "dummy-request-id"

    # Provide actual upload ID in place of __UPLOAD_ID__
    upload_id = "__UPLOAD_ID__"

    obj_data_generator = MultipartObjectDataGenerator(
        logger, config.object_size, total_parts)

    obj = S3AsyncUploadPart(session, request_id,
                            bucket_name, object_name,
                            upload_id)

    total_chunks = int(config.object_size / total_parts)
    print("Total chunks {}".format(total_chunks))

    for part_no in range(1, int(total_parts + 1)):
        await obj.upload(obj_data_generator, part_no, total_chunks)
        print("\n")

    logger.info("S3AsyncUploadPart test passed!")
    await session.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
