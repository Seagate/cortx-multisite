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

import logging
from s3replicationcommon.job import ReplicationJobType
from s3replicationcommon.job import JobEvents
from s3replicationcommon.s3_head_object import S3AsyncHeadObject
from .multipart_object_replicator import MultipartObjectReplicator
from .object_replicator import ObjectReplicator
from .object_tag_replicator import ObjectTagReplicator
from .session_manager import get_session

_logger = logging.getLogger('s3replicator')


class TranferEventHandler:
    def __init__(self, app) -> None:
        """Initialise."""
        self._app = app

    async def notify(self, event, job_id):
        """Handles a given JobEvent.

        Args:
            event (JobEvents): Job event enum value.
            job (Job): Job for which event is handled.
        """
        job = None
        if event == JobEvents.COMPLETED:
            _logger.debug("Processing job completed event for job id[{}]".
                          format(job_id))
            # Release completed job from job list.
            job = self._app['all_jobs'].remove_job_by_job_id(job_id)
            if job is not None:
                job.mark_completed()
                _logger.debug(
                    "Removed job from app['all_jobs'] for job_id {}".
                    format(job_id))
                if self._app["config"].job_cache_enabled:
                    # cache it, so status can be queried.
                    _logger.debug("Moved job after completion for job_id {}"
                                  " to app['completed_jobs']".format(job_id))
                    self._app['completed_jobs'].add_job(job)

                # Update the replication manager about job completion.
                # XXX Support to pick out of multiple replication managers.
                replication_manager = \
                    list(self._app['replication-managers'].values())[0]

                # In tests, replication manager acks are not required.
                if job.get_remote_job_id() is not None:
                    await replication_manager.send_update(
                        job.get_remote_job_id(),
                        "completed")


class TransferInitiator:
    async def start(job, app):
        operation_type = job.get_operation_type()
        _logger.debug("Replication operation = {}".format(operation_type))
        app_config = app["config"]

        # Reuse the sessions.
        source_session = get_session(
            app,
            job.get_source_s3_site(),
            job.get_source_access_key(),
            job.get_source_secret_key(),
            app_config.max_connections_per_s3_session)

        target_session = get_session(
            app,
            job.get_target_s3_site(),
            job.get_target_access_key(),
            job.get_target_secret_key(),
            app_config.max_connections_per_s3_session)

        # For Cortx, default value of version_id=None
        head_object = S3AsyncHeadObject(source_session, job.get_job_id(),
                                        job.get_source_bucket_name(), job.get_source_object_name(),
                                        None)

        await head_object.get(None)

        source_etag = head_object.get_etag()
        _logger.info("Source ETag : {}".format(source_etag))

        # List to store ETag of each parts of source object
        part_length = []

        # "-" in source ETag indicates multipart object upload
        if "-" in source_etag:
            # Get the total part count and object size
            total_parts = source_etag.split("-")[1][0]
            object_size = head_object.get_content_length()
            _logger.debug("Total Parts : {}".format(total_parts))
            _logger.debug("Content length : {}".format(object_size))

            # calculate single part length
            part_len = object_size / int(total_parts)

            # Append the length of each part into the list
            # Pass the list to multipart object replicator class
            for part_no in range(1, int(total_parts) + 1):
                _logger.debug("Part No : {}".format(part_no))
                part_length.append(int(part_len))

            # Future reference code, after getting updated head object and get object api
            # Get the specific part information using head object by passing part number
            # for part_no in range(1, int(total_parts)+1):
            #     await head_object.get(part_no)
            #     part_length.append(head_object.get_content_length())

            _logger.info("Part content length list : {}".format(part_length))

            if operation_type == ReplicationJobType.OBJECT_REPLICATION:
                multipart_obj_replicator = MultipartObjectReplicator(
                    job, app["config"].transfer_chunk_size_bytes,
                    source_session, target_session, total_parts, part_length)
                multipart_obj_replicator.setup_observers(
                    "all_events", TranferEventHandler(app))

            job.set_replicator(multipart_obj_replicator)
            job.mark_started()

            # Start the multipart replication.
            semaphore = app['semaphore']
            async with semaphore:
                await multipart_obj_replicator.start()

        # If the head object returns ETag without part number
        # Then it could be a simple object or tag replication
        # based on the value of 'replication job type'.
        else:
            if operation_type == ReplicationJobType.OBJECT_REPLICATION:
                object_replicator = ObjectReplicator(
                    job, app["config"].transfer_chunk_size_bytes,
                    app["config"].range_read_offset,
                    app["config"].range_read_length,
                    source_session, target_session)
                object_replicator.setup_observers(
                    "all_events", TranferEventHandler(app))

                job.set_replicator(object_replicator)
                job.mark_started()

                # Start the simple object replication.
                semaphore = app['semaphore']
                async with semaphore:
                    await object_replicator.start()

            elif operation_type == ReplicationJobType.OBJECT_TAGS_REPLICATION:
                object_tag_replicator = ObjectTagReplicator(
                    job, source_session, target_session)
                object_tag_replicator.setup_observers(
                    "all_events", TranferEventHandler(app))

                job.set_replicator(object_tag_replicator)
                job.mark_started()

                # Start the tag replication.
                semaphore = app['semaphore']
                async with semaphore:
                    await object_tag_replicator.start()
            else:
                _logger.error(
                    "Operation type [{}] not supported.".format(operation_type))
                return None
