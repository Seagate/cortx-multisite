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
from .replicate_object import ReplicateObject

_logger = logging.getLogger('s3replicator')


class TranferEventHandler:
    def __init__(self, app) -> None:
        """Initialise"""
        self._app = app

    def notify(self, event, job_id):
        """Handles a given JobEvent

        Args:
            event (JobEvents): Job event enum value.
            job (Job): Job for which event is handled.
        """
        if event == JobEvents.COMPLETED:
            _logger.debug("Processing job completed event for job id[{}]".
                          format(job_id))
            # Release completed job from job list.
            self._app['all_jobs'].remove_job_by_job_id(job_id)


class TransferInitiator:
    async def start(job, app):
        operation_type = job.get_operation_type()
        _logger.debug("Replication operation = {}".format(operation_type))
        if operation_type == ReplicationJobType.OBJECT_REPLICATION:
            object_replicator = ReplicateObject(
                job, app["config"].transfer_chunk_size_bytes)
            object_replicator.setup_observers(
                "all_events", TranferEventHandler(app))

            job.set_replicator(object_replicator)

            # Start the replication.
            await object_replicator.start()
        else:
            _logger.error(
                "Operation type [{}] not supported.".format(operation_type))
            return None
