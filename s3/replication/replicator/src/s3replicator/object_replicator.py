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
from s3replicationcommon.job import JobEvents
from s3replicationcommon.s3_site import S3Site
from s3replicationcommon.s3_session import S3Session
from s3replicationcommon.s3_common import S3RequestState
from s3replicationcommon.s3_get_object import S3AsyncGetObject
from s3replicationcommon.s3_put_object import S3AsyncPutObject

_logger = logging.getLogger('s3replicator')


class ObjectReplicator:
    def __init__(self, job, transfer_chunk_size_bytes) -> None:
        """Initialise"""

        self._transfer_chunk_size_bytes = transfer_chunk_size_bytes
        self._job_id = job.get_job_id()

        # A set of observers to watch for varius notifications.
        # To start with job completed (success/failure)
        self._observers = {}

        # Setup source site info
        self._s3_source_site = S3Site(
            job.get_source_endpoint(),
            job.get_source_s3_service_name(),
            job.get_source_s3_region())

        self._s3_source_session = S3Session(
            _logger,
            self._s3_source_site,
            job.get_source_access_key(),
            job.get_source_secret_key())

        self._object_reader = S3AsyncGetObject(
            self._s3_source_session,
            job.get_source_bucket_name(),
            job.get_source_object_name(),
            int(job.get_source_object_size()))

        # Setup target site info
        self._s3_target_site = S3Site(
            job.get_target_endpoint(),
            job.get_target_s3_service_name(),
            job.get_target_s3_region())

        self._s3_target_session = S3Session(
            _logger,
            self._s3_target_site,
            job.get_target_access_key(),
            job.get_target_secret_key())

        self._object_writer = S3AsyncPutObject(
            self._s3_target_session,
            job.get_target_bucket_name(),
            job.get_source_object_name(),
            int(job.get_source_object_size()))

    def setup_observers(self, label, observer):
        self._observers[label] = observer

    async def start(self):
        # Start transfer
        await self._object_writer.send(self._object_reader,
                                       self._transfer_chunk_size_bytes)
        # notify job state events
        for label, observer in self._observers.items():
            _logger.debug(
                "Notify completion to observer with label[{}]".format(label))
            if self._object_writer.get_state() == S3RequestState.PAUSED:
                observer.notify(JobEvents.STOPPED, self._job_id)
            elif self._object_writer.get_state() == S3RequestState.ABORTED:
                observer.notify(JobEvents.ABORTED, self._job_id)
            else:
                observer.notify(JobEvents.COMPLETED, self._job_id)

        # Once the replication is complete, close session.
        # XXX Extend to reuse sessions for multiple replications.
        await self._s3_source_session.close()
        await self._s3_target_session.close()

    def pause(self):
        """Pause the running object tranfer"""
        pass  # XXX

    def resume(self):
        """Resume the running object tranfer"""
        pass  # XXX

    def abort(self):
        """Abort the running object tranfer"""
        self._object_writer.abort()
