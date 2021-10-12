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
import hashlib
import os
import sys
import time
import uuid
import yaml
from random import randrange
from s3replicationcommon.s3_put_object import S3AsyncPutObject
from s3replicationcommon.s3_put_object_tagging import S3AsyncPutObjectTagging
from s3replicationcommon.s3_site import S3Site
from s3replicationcommon.s3_session import S3Session
from s3replicationcommon.log import setup_logger
from s3replicationcommon.s3_common import S3RequestState
from s3replicationcommon.templates import fdmi_record_template
from s3replicationcommon.templates import fdmi_record_tag_template
from s3replicationmanager.config import Config as ManagerConfig
from s3_config import S3Config


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


# Helper methods


def init_logger():
    log_config_file = os.path.join(os.path.dirname(__file__),
                                   'config', 'logger_config.yaml')

    print("Using log config {}".format(log_config_file))
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        print("Failed to configure logging.\n")
        sys.exit(-1)
    return logger


def create_job_with_fdmi_record(s3_config, test_config, object_info):
    job_dict = fdmi_record_tag_template()

    # Update the fields in template.
    # XXX Removed md5 and lenght
    job_dict["Bucket-Name"] = test_config.source_bucket
    job_dict["Object-Name"] = object_info["object_name"]
    job_dict["Object-URI"] = test_config.source_bucket + \
        '\\\\' + object_info["object_name"]
    job_dict["User-Defined"]["x-amz-meta-target-site"] = \
        s3_config.s3_service_name
    job_dict["User-Defined"]["x-amz-meta-target-bucket"] = \
        test_config.target_bucket

    return job_dict


async def async_put_object_tagging(session, bucket_name, object_name, tag_set):

    request_id = str(uuid.uuid4())

    obj = S3AsyncPutObjectTagging(session, request_id, bucket_name,
                                  object_name, tag_set)

    await obj.send()

    status = "success"
    # Start transfer
    # if object_writer.get_state() != S3RequestState.COMPLETED:
    #    status = "failed"

    return {"object_name": object_name, "status": status}


async def setup_source(session, test_config):
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

        tagset = {}

        # Generate object name
        object_name = "test_object_" + str(i) + "_sz" + str(object_size)

        # Adding 2 exmaple tags to tagset to replicate
        for i in range(2):
            tag_name = object_name + "-tag-" + str(i)
            tag_value = object_name + "-value-" + str(i)
            tagset[tag_name]=tag_value

        # Perform the PUT operation on source and capture md5.
        task = asyncio.ensure_future(
            async_put_object_tagging(session, test_config.source_bucket, object_name, tagset))
        put_task_list.append(task)
    objects_info = await asyncio.gather(*put_task_list)
    return objects_info


async def run_load_test():
    manager_config_file = os.path.join(
        os.path.dirname(__file__), '..', '..', 'src', 'config',
        'config.yaml')
    manager_config = ManagerConfig(manager_config_file)
    manager_config.load()
    # URL for non-secure http endpoint
    url = 'http://' + manager_config.host + \
        ':' + str(manager_config.port)

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

    # Put data on source
    objects_info = await setup_source(s3_session, test_config)

    manager_session = aiohttp.ClientSession()
    # Post replication jobs to manager.
    transfer_task_list = []
    for object_info in objects_info:
        if object_info["status"] == "failed":
            logger.error("\n\nFailed preparing source object!\n")
            sys.exit(-1)
        manager_job = create_job_with_fdmi_record(
            s3_config, test_config, object_info)
        logger.debug("POST {}/jobs {}".format(url, manager_job))
        transfer_task = asyncio.ensure_future(manager_session.post(
            url + '/jobs', json=manager_job))
        transfer_task_list.append(transfer_task)
    # jobs info contains list of response from POST /jobs for each transfer
    logger.debug("Waiting for all POST {}/jobs response...".format(url))
    post_jobs_response_list = await asyncio.gather(*transfer_task_list)
    logger.debug("post_jobs_response_list: {}".format(
        post_jobs_response_list))

    # Prepare a list of posted job_id's
    posted_jobs_set = set()
    for post_job_resp in post_jobs_response_list:
        job_status = await post_job_resp.json()
        logger.debug("job_status: {}".format(job_status))
        job_id = job_status['job_id']

        posted_jobs_set.add(job_id)

    # Poll for replication jobs completion.
    jobs_running = True  # if at least one job is running, keep polling.
    # Max polling iterations to avoid infinite loop
    polling_count = test_config.polling_count

    async with manager_session.get(url + '/jobs?count&completed') as resp:
        logger.info(
            'GET jobs returned http Status: {}'.format(resp.status))
        response = await resp.json()
        manager_completed_count = response['count']
    logger.info("Present jobs completed by manager : {}".format(
        manager_completed_count))

    while jobs_running and polling_count != 0:

        completed_count = 0

        async with manager_session.get(url + '/jobs?count&completed') as resp:
            logger.info(
                'GET jobs returned http Status: {}'.format(resp.status))
            response = await resp.json()
            completed_count = response['count']

        logger.info("completed jobs count : {}".format(completed_count))

        if completed_count == (
                test_config.count_of_obj + manager_completed_count):
            # No jobs pending then exit here.
            jobs_running = False
            logger.info("All jobs completed.")
            sys.exit(0)

        else:
            # There are atleast some running jobs, give time to complete.
            logger.debug(
                "Pending status for total {} jobs.".format(
                    (test_config.count_of_obj + manager_completed_count) - completed_count))
            logger.info("Waiting for {} secs before polling job status...".
                        format(test_config.polling_wait_time))
            time.sleep(test_config.polling_wait_time)

        polling_count -= 1

    # Execute this if all jobs are not completed.
    inprogress_count = 0
    queued_count = 0

    # Get inprogress jobs count
    async with manager_session.get(url + '/jobs?count&inprogress') as resp:
        logger.info(
            'GET jobs returned http Status: {}'.format(resp.status))
        response = await resp.json()

        inprogress_count = response['count']
        logger.info("In-progress jobs count : {}".format(inprogress_count))

    async with manager_session.get(url + '/jobs?count&queued') as resp:
        logger.info(
            'GET jobs returned http Status: {}'.format(resp.status))
        response = await resp.json()

        queued_count = response['count']
        logger.info("Queueud jobs count: {}".format(queued_count))

    logger.info(
        "Pending jobs count : {}".format(
            queued_count +
            inprogress_count))
    logger.info("To get in-progress jobs :\n '{}/jobs?inprogress'".format(url))
    logger.info("To get queued jobs :\n '{}/jobs?queued'".format(url))

    await s3_session.close()
    await manager_session.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_load_test())
