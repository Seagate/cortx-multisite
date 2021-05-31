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

# Goal of tests in this file is to generate high number of source objects
# Transfer all the objects at target and verify target objects existence
# and data integrity using md5 match

import asyncio
import hashlib
import os
import sys
from random import randrange
from s3replicationcommon.s3_put_object import S3AsyncPutObject
from s3replicationcommon.s3_site import S3Site
from s3replicationcommon.s3_session import S3Session
from s3replicationcommon.log import setup_logger
from s3replicator.config import Config as ReplicatorConfig
from .s3_config import S3Config

class TestConfig:
    count_of_obj = 100
    min_obj_size = 1024  # 1k - size in bytes
    max_obj_size = 100 * 1024 * 1024 # 100MB - size in bytes
    source_bucket = "sourcebucket"
    target_bucket = "targetbucket"

# Helper methods
class ObjectDataGenerator:
    def __init__(self, object_size):
        """Initialise."""
        self._object_size = object_size
        self._hash = hashlib.md5()

    async def fetch(self, chunk_size):
        total_chunks = int(self._object_size / chunk_size)
        pending_size = self._object_size
        #  Generate only one chunk and just keep sending same for each iteration
        data = os.urandom(chunk_size)
        for _ in range(0, total_chunks):
          if pending_size >= chunk_size:
              pending_size -= chunk_size
              self._hash.update(data)
              yield data
          else:
              # pending size is less than chunk size, generate only pending size
              last_data = os.urandom(pending_size)
              self._hash.update(last_data)
              yield last_data
              pending_size = 0
        self._md5 = self._hash.hexdigest()

def get_logger():
    log_config_file = os.path.join(os.path.dirname(__file__),
                                   'config', 'logger_config.yaml')

    print("Using log config {}".format(log_config_file))
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        print("Failed to configure logging.\n")
        sys.exit(-1)
    return logger

def create_replication_job(object_name, object_info):
    pass  # XXX TBD

async def async_put_object(session, bucket_name, object_name, object_size,
                           transfer_chunk_size):

    object_reader = ObjectDataGenerator(object_size)
    object_writer = S3AsyncPutObject(session, bucket_name,
                                     object_name, object_size)

    # Start transfer
    await object_writer.send(object_reader, transfer_chunk_size)
    return { object_name: {"size": object_size, "md5": object_reader.get_md5()} }


async def setup_source(session, bucket_name, transfer_chunk_size):
    # Create objects at source and returns map with object info

    # {"object-name1": {size: 4096, md5: abcd},
    #  "object-name2": {size: 8192, md5: pqr}}
    put_task_list = []
    for i in range(TestConfig.count_of_obj):
        # Generate random object size
        object_size = randrange(TestConfig.min_obj_size, TestConfig.max_obj_size)

        # Generate object name
        object_name = "test_object_" + str(object_size)

        # Perform the PUT operation on source and capture md5.
        task = asyncio.create_task(
                  async_put_object(session, bucket_name, object_name,
                    object_size, transfer_chunk_size))
        put_task_list.append(task)
    objects_info = await asyncio.gather(*put_task_list)
    return objects_info


async def run_load_test():
    replicator_config = ReplicatorConfig()
    replicator_config.load()
    # URL for non-secure http endpoint
    url = 'http://' + replicator_config.host + ':' + replicator_config.port

    s3_config = S3Config()
    s3_site = S3Site(s3_config.endpoint, s3_config.s3_service_name, s3_config.s3_region)

    session = S3Session(get_logger(), s3_site, s3_config.access_key, s3_config.secret_key)

    # Prepare the source data
    objects_info = await setup_source(session, s3_config.source_bucket_name, s3_config.transfer_chunk_size)

    # Post replication jobs.
    transfer_task_list = []
    for object_name, object_info in objects_info.items():
        replication_job = create_replication_job(object_name, object_info)
        transfer_task = asyncio.create_task(session.post(
                url + '/jobs', json=replication_job))
        transfer_task_list.append(transfer_task)
    jobs_info = await asyncio.gather(*transfer_task_list)

    # Poll for replication jobs completion.
    for job_id in jobs_info:
        pass  # XXX TBD

    await session.close()