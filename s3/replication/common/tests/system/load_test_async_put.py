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
from config import Config
import os
import sys
from object_generator import FixedObjectDataGenerator
from s3replicationcommon.s3_common import S3RequestState
from s3replicationcommon.log import setup_logger
from s3replicationcommon.s3_site import S3Site
from s3replicationcommon.s3_session import S3Session
from s3replicationcommon.s3_put_object import S3AsyncPutObject


async def main():

    config = Config()

    bucket_name = "sourcebucket"
    total_count = 200  # Number of objects to upload.
    object_size = 4096  # Bytes.

    # Setup logging and get logger
    log_config_file = os.path.join(os.path.dirname(__file__),
                                   'config', 'logger_config.yaml')

    print("Using log config {}".format(log_config_file))
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        print("Failed to configure logging.\n")
        sys.exit(-1)

    s3_site = S3Site(config.endpoint, config.s3_service_name, config.s3_region)

    session = S3Session(
        logger,
        s3_site,
        config.access_key,
        config.secret_key,
        config.max_s3_connections)

    reader_list = []
    writer_list = []
    # Prepare for upload.
    for i in range(total_count):
        # Generate object name
        object_name = "test_object_" + str(i) + "_sz" + str(object_size)

        request_id = "request-id" + str(i)
        object_reader = FixedObjectDataGenerator(
            logger, object_name, object_size)
        object_writer = S3AsyncPutObject(session, request_id, bucket_name,
                                         object_name, object_size)
        reader_list.append(object_reader)
        writer_list.append(object_writer)

    put_task_list = []
    # Trigger upload.
    for i in range(total_count):
        task = asyncio.ensure_future(
            writer_list[i].send(reader_list[i], reader_list[i].object_size))
        put_task_list.append(task)

    # Wait for uploads to complete.
    upload_states = await asyncio.gather(*put_task_list)

    total_time_ms = 0
    index = 0
    for state in upload_states:
        # Validate object uploaded successfully.
        assert state == S3RequestState.COMPLETED

        upload_etag = writer_list[index].get_response_header("Etag").strip('"')
        data_md5 = reader_list[index].get_md5()
        assert upload_etag == data_md5, \
            "PUT Etag = {} and Data MD5 = {}".format(upload_etag, data_md5)

        total_time_ms += writer_list[index].get_execution_time()

        index += 1

    logger.info("Total time to upload {} objects = {} ms.".format(
        total_count, total_time_ms))
    logger.info("Avg time per upload = {} ms.".format(
        total_time_ms / total_count))

    await session.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
