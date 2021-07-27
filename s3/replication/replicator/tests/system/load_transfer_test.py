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


import aiohttp
import asyncio
import datetime
import hashlib
import os
import sys
import time
import uuid
import yaml
from random import randrange
from s3replicationcommon.s3_put_object import S3AsyncPutObject
from s3replicationcommon.s3_site import S3Site
from s3replicationcommon.s3_session import S3Session
from s3replicationcommon.log import setup_logger
from s3replicationcommon.s3_common import S3RequestState
from s3replicationcommon.templates import replication_job_template
from s3replicator.config import Config as ReplicatorConfig
from s3_config import S3Config


# Helper methods


class TestConfig:
    """Configuration for load transfer test."""

    def __init__(self):
        """Initialise."""
        # Read the test config fite.
        with open(os.path.join(os.path.dirname(__file__),
                  'config/load_transfer_test_config.yaml'), 'r') as config:
            self._config = yaml.safe_load(config)

        self.count_of_obj = self._config["count_of_obj"]
        self.min_obj_size = self._config["min_obj_size"]
        self.max_obj_size = self._config["max_obj_size"]
        self.fixed_size = self._config["fixed_size"]
        self.random_size_enabled = self._config["random_size_enabled"]
        self.source_bucket = self._config["source_bucket"]
        self.target_bucket = self._config["target_bucket"]
        self.polling_wait_time = self._config["polling_wait_time"]
        self.polling_count = self._config["polling_count"]


class ObjectDataGenerator:
    def __init__(self, logger, object_name, object_size):
        """Initialise."""
        self._logger = logger
        self._object_name = object_name
        self._object_size = object_size
        self._hash = hashlib.md5()
        self._state = S3RequestState.INITIALISED

    def get_state(self):
        """Returns current request state."""
        return self._state

    def get_etag(self):
        if self._state == S3RequestState.COMPLETED:
            return self._md5
        return None

    async def fetch(self, chunk_size):
        pending_size = self._object_size
        # Generate only one chunk and just keep sending same for each iteration
        data = os.urandom(chunk_size)
        self._state = S3RequestState.RUNNING
        self._logger.debug("Start data gen. pending_size {} bytes.".
                           format(pending_size))
        while pending_size > 0:
            if pending_size >= chunk_size:
                pending_size -= chunk_size
                self._hash.update(data)
                self._logger.debug("pending_size {} bytes.".
                                   format(pending_size))
                self._logger.debug("Yielding data of size {} bytes.".
                                   format(chunk_size))
                yield data
            else:
                # pending size is less than chunk size, generate only pending
                # size
                last_data = os.urandom(pending_size)
                self._hash.update(last_data)
                self._logger.debug(
                    "Yielding last unit of data of size {} bytes.".
                    format(pending_size))
                yield last_data
                pending_size = 0
        self._logger.debug("Data generation completed for object {}.".
                           format(self._object_name))
        self._md5 = self._hash.hexdigest()
        self._state = S3RequestState.COMPLETED


def init_logger():
    log_config_file = os.path.join(os.path.dirname(__file__),
                                   'config', 'logger_config.yaml')

    print("Using log config {}".format(log_config_file))
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        print("Failed to configure logging.\n")
        sys.exit(-1)
    return logger


def create_replication_job(s3_config, test_config, object_info):
    job_dict = replication_job_template()
    # Update the fields in template.
    epoch_t = datetime.datetime.utcnow()
    job_dict["replication-id"] = test_config.source_bucket + \
        object_info["object_name"] + str(epoch_t)
    job_dict["replication-event-create-time"] = epoch_t.strftime(
        '%Y%m%dT%H%M%SZ')

    job_dict["source"]["endpoint"] = s3_config.endpoint
    job_dict["source"]["service_name"] = s3_config.s3_service_name
    job_dict["source"]["region"] = s3_config.s3_region
    job_dict["source"]["access_key"] = s3_config.access_key
    job_dict["source"]["secret_key"] = s3_config.secret_key

    job_dict["source"]["operation"]["attributes"]["Bucket-Name"] = \
        test_config.source_bucket
    job_dict["source"]["operation"]["attributes"]["Object-Name"] = \
        object_info["object_name"]
    job_dict["source"]["operation"]["attributes"]["Content-Length"] = \
        object_info["size"]
    job_dict["source"]["operation"]["attributes"]["Content-MD5"] = \
        object_info["md5"]

    job_dict["target"]["endpoint"] = s3_config.endpoint
    job_dict["target"]["service_name"] = s3_config.s3_service_name
    job_dict["target"]["region"] = s3_config.s3_region
    job_dict["target"]["access_key"] = s3_config.access_key
    job_dict["target"]["secret_key"] = s3_config.secret_key

    job_dict["target"]["Bucket-Name"] = test_config.target_bucket

    return job_dict


async def async_put_object(session, bucket_name, object_name, object_size,
                           transfer_chunk_size):

    request_id = str(uuid.uuid4())

    object_reader = ObjectDataGenerator(session.logger,
                                        object_name, object_size)
    object_writer = S3AsyncPutObject(session, request_id, bucket_name,
                                     object_name, object_size)

    status = "success"
    # Start transfer
    await object_writer.send(object_reader, transfer_chunk_size)
    if object_writer.get_state() != S3RequestState.COMPLETED:
        status = "failed"

    return {"object_name": object_name, "size": object_size,
            "md5": object_reader.get_etag(),
            "etag": object_writer.get_response_header("ETag"),
            "status": status
            }


async def setup_source(session, test_config, transfer_chunk_size):
    # Create objects at source and returns list with object info

    # [{"object_name": "object-name1", "size": 4096, "md5": abcd},
    #  {"object_name": "object-name2", "size": 8192, "md5": pqrs}]
    put_task_list = []
    for i in range(test_config.count_of_obj):
        # Generate object size
        object_size = test_config.fixed_size
        if test_config.random_size_enabled:
            object_size = randrange(
                test_config.min_obj_size,
                test_config.max_obj_size)

        # Generate object name
        object_name = "test_object_" + str(i) + "_sz" + str(object_size)

        # Perform the PUT operation on source and capture md5.
        task = asyncio.ensure_future(
            async_put_object(session, test_config.source_bucket, object_name,
                             object_size, transfer_chunk_size))
        put_task_list.append(task)
    objects_info = await asyncio.gather(*put_task_list)
    return objects_info


async def run_load_test():
    replicator_config_file = os.path.join(
        os.path.dirname(__file__), '..', '..', 'src', 'config',
        'config.yaml')
    replicator_config = ReplicatorConfig(replicator_config_file)
    replicator_config.load()
    # URL for non-secure http endpoint
    url = 'http://' + replicator_config.host + \
        ':' + str(replicator_config.port)

    logger = init_logger()

    test_config = TestConfig()

    s3_config = S3Config()
    s3_site = S3Site(
        s3_config.endpoint,
        s3_config.s3_service_name,
        s3_config.s3_region)

    s3_session = S3Session(
        logger,
        s3_site,
        s3_config.access_key,
        s3_config.secret_key)

    # Prepare the source data
    objects_info = await setup_source(s3_session, test_config,
                                      s3_config.transfer_chunk_size)

    replicator_session = aiohttp.ClientSession()
    # Post replication jobs.
    transfer_task_list = []
    for object_info in objects_info:
        if object_info["status"] == "failed":
            logger.error("\n\nFailed preparing source object!\n")
            sys.exit(-1)
        replication_job = create_replication_job(
            s3_config, test_config, object_info)
        replication_jobs = [replication_job]
        logger.debug("POST {}/jobs {}".format(url, replication_jobs))
        transfer_task = asyncio.ensure_future(replicator_session.post(
            url + '/jobs', json=replication_jobs))
        transfer_task_list.append(transfer_task)
    # jobs info contains list of response from POST /jobs for each transfer
    logger.debug("Waiting for all POST {}/jobs response...".format(url))
    post_jobs_response_list = await asyncio.gather(*transfer_task_list)
    logger.debug("post_jobs_response_list: {}".format(
        post_jobs_response_list))

    # Prepare a list of posted job_id's
    # Not required TODO -- OR -- Can be used with in_prgoress_list later
    posted_jobs_set = set()
    for post_job_resp in post_jobs_response_list:
        job_status = await post_job_resp.json()
        logger.debug("job_status: {}".format(job_status))
        accepted_job = job_status["accepted_jobs"][0]
        job_id = list(accepted_job.values())[0]
        replication_id = list(accepted_job.keys())[0]
        logger.debug("Posted job details: job_id [{}], replication-id [{}]".
                     format(job_id, replication_id))

        posted_jobs_set.add(job_id)

    # Poll for replication jobs completion.
    jobs_running = True  # if at least one job is running, keep polling.
    # Max polling iterations to avoid infinite loop
    polling_count = test_config.polling_count

    response = {}
    while jobs_running and polling_count != 0:
        async with replicator_session.get(
                url + '/jobs?count&inprogress') as resp:
            logger.info(
                'GET jobs returned http Status: {}'.format(resp.status))
            response = await resp.json()

        inprogress_count = response['inprogress-count']
        logger.info("In-progress jobs count : {}".format(inprogress_count))

        if inprogress_count == 0:
            # No jobs pending then exit here.
            jobs_running = False
            logger.debug("All jobs completed.")
            sys.exit(0)
        else:
            # There are atleast some running jobs, give time to complete.
            logger.debug(
                "Pending status for total {} jobs.".format(
                    inprogress_count))
            logger.info("Waiting for {} secs before polling job status...".
                        format(test_config.polling_wait_time))
            time.sleep(test_config.polling_wait_time)

        polling_count -= 1

    logger.info(
        "To get in-progress jobs : '{}/jobs?inprogress'".format(url))

    await s3_session.close()
    await replicator_session.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_load_test())
