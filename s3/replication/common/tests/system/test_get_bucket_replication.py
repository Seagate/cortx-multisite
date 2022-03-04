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
# s3 get-bucket-replication api test script
# Usage : python3 test_s3_get_bucket_replication.py
#

import asyncio
import os
import sys
from config import Config
from s3replicationcommon.log import setup_logger
from s3replicationcommon.s3_site import S3Site
from s3replicationcommon.s3_session import S3Session
from s3replicationcommon.s3_get_bucket_replication \
    import S3AsyncGetBucketReplication


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

    # Read configs for future comparision
    replication_prefix = str(config.object_name_prefix)
    test_replication_object = replication_prefix
    replication_dest_bucket = config.target_bucket_name

    s3_site = S3Site(config.endpoint, config.s3_service_name, config.s3_region)

    session = S3Session(logger, s3_site, config.access_key, config.secret_key)

    # Generate object names
    request_id = "dummy-request-id"
    obj = S3AsyncGetBucketReplication(
        session, request_id, config.source_bucket_name)

    # Start transfer
    await obj.get()

    replication_rule = obj.get_replication_rule(test_replication_object)
    logger.debug(replication_rule)

    assert replication_rule._prefix == replication_prefix, \
        "replication_prefix mismatched"
    assert replication_rule._dest_bucket == replication_dest_bucket, \
        "replication_dest_bucket mismatched"

    await session.close()

    logger.info("AsyncS3GetBucketReplication test passed!")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
