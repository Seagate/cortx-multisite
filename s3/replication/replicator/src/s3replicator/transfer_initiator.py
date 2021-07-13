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
from .object_replicator import ObjectReplicator
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

        if operation_type == ReplicationJobType.OBJECT_REPLICATION:
            object_replicator = ObjectReplicator(
                job, app["config"].transfer_chunk_size_bytes,
                source_session, target_session)
            object_replicator.setup_observers(
                "all_events", TranferEventHandler(app))

            job.set_replicator(object_replicator)
            job.mark_started()

            # Start the replication.
            semaphore = app['semaphore']
            async with semaphore:
                await object_replicator.start()
        else:
            _logger.error(
                "Operation type [{}] not supported.".format(operation_type))
            return None
