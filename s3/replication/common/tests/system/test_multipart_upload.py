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
from object_generator_multipart_upload import MultipartObjectDataGenerator
from s3replicationcommon.log import setup_logger
from s3replicationcommon.s3_site import S3Site
from s3replicationcommon.s3_session import S3Session
from s3replicationcommon.s3_create_multipart_upload \
    import S3AsyncCreateMultipartUpload
from s3replicationcommon.s3_upload_part import S3AsyncUploadPart
from s3replicationcommon.s3_complete_multipart_upload \
    import S3AsyncCompleteMultipartUpload


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

    source_bucket_name = config.source_bucket_name
    # Generate object names
    source_object_name = str(config.object_name_prefix)
    request_id = "dummy-request-id"

    total_parts = config.total_parts

    # Start Multipart Upload
    # Create multipart
    print("\nCreate multipart upload")
    print("_______________________\n")
    obj_create = S3AsyncCreateMultipartUpload(
        session, request_id, source_bucket_name, source_object_name)

    await obj_create.create()
    upload_id = obj_create.get_response_header("UploadId")

    # Object data generator
    obj_data_generator = MultipartObjectDataGenerator(
        logger, config.object_size, total_parts)

    # Upload part
    print("\nUpload part")
    print("___________\n")
    obj_upload = S3AsyncUploadPart(session, request_id,
                                   source_bucket_name, source_object_name,
                                   upload_id)

    total_chunks = int(config.object_size / total_parts)

    for part_no in range(1, int(total_parts + 1)):
        await obj_upload.upload(obj_data_generator, part_no, total_chunks)
        print("\n")

    etag_dict = obj_upload.get_etag_dict()

    # Complete multipart upload
    print("Complete multipart upload")
    print("__________________________\n")
    obj_complete = S3AsyncCompleteMultipartUpload(session, request_id,
                                                  source_bucket_name,
                                                  source_object_name,
                                                  upload_id, etag_dict)

    await obj_complete.complete_upload()

    final_etag = obj_complete.get_final_etag()
    logger.info("Final ETag : {}".format(final_etag))

    logger.info("S3AsyncMultipartUpload test passed!")
    await session.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
