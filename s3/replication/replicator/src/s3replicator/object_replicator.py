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
from s3replicationcommon.s3_common import S3RequestState
from s3replicationcommon.s3_get_object import S3AsyncGetObject
from s3replicationcommon.s3_put_object import S3AsyncPutObject
from s3replicationcommon.s3_update_replication_status import S3AsyncUpdatereplicationStatus
from s3replicationcommon.timer import Timer

_logger = logging.getLogger('s3replicator')


class ObjectReplicator:
    def __init__(self, job, transfer_chunk_size_bytes, range_read_offset,
                 range_read_length, source_session, target_session) -> None:
        """Initialise."""
        self._transfer_chunk_size_bytes = transfer_chunk_size_bytes
        self._job_id = job.get_job_id()
        self._request_id = self._job_id
        self._timer = Timer()
        self._range_read_offset = range_read_offset
        self._range_read_length = range_read_length

        # A set of observers to watch for varius notifications.
        # To start with job completed (success/failure)
        self._observers = {}

        self._s3_source_session = source_session

        self._object_source_reader = S3AsyncGetObject(
            self._s3_source_session,
            self._request_id,
            job.get_source_bucket_name(),
            job.get_source_object_name(),
            int(job.get_source_object_size()),
            self._range_read_offset,
            self._range_read_length)

        self._source_replication_status = S3AsyncUpdatereplicationStatus(
            self._s3_source_session,
            self._request_id,
            job.get_source_owner_account_id(),
            job.get_source_bucket_name(),
            job.get_source_object_name())

        # Setup target site info
        self._s3_target_session = target_session

        self._object_writer = S3AsyncPutObject(
            self._s3_target_session,
            self._request_id,
            job.get_target_bucket_name(),
            job.get_source_object_name(),
            int(job.get_source_object_size()))

        self._object_target_reader = S3AsyncGetObject(
            self._s3_target_session,
            self._request_id,
            job.get_target_bucket_name(),
            job.get_source_object_name(),
            int(job.get_source_object_size()),
            self._range_read_offset,
            self._range_read_length)

    def get_execution_time(self):
        """Return total time for Object replication."""
        return self._timer.elapsed_time_ms()

    def setup_observers(self, label, observer):
        self._observers[label] = observer

    async def start(self):
        # Start transfer
        self._timer.start()
        await self._object_writer.send(self._object_source_reader,
                                       self._transfer_chunk_size_bytes)
        self._timer.stop()
        _logger.info(
            "Replication completed in {}ms for job_id {}".format(
                self._timer.elapsed_time_ms(), self._job_id))

        # notify job state events
        for label, observer in self._observers.items():
            _logger.debug(
                "Notify completion to observer with label[{}]".format(label))
            if self._object_writer.get_state() == S3RequestState.PAUSED:
                await observer.notify(JobEvents.STOPPED, self._job_id)
            elif self._object_writer.get_state() == S3RequestState.ABORTED:
                await observer.notify(JobEvents.ABORTED, self._job_id)
            else:
                await observer.notify(JobEvents.COMPLETED, self._job_id)

        if JobEvents.COMPLETED:
            await self._source_replication_status.update('COMPLETED')

            source_etag = self._object_source_reader.get_etag()
            target_etag = self._object_writer.get_etag()

            _logger.info(
                "MD5 : Source {} and Target {}".format(
                    source_etag, target_etag))

            # check md5 of source and replicated objects at target
            if source_etag == target_etag:
                _logger.info("MD5 matched for job_id {}".format(self._job_id))
            else:
                _logger.error(
                    "MD5 not matched for job_id {}".format(
                        self._job_id))

            # check content length of source and target objects
            # [system-defined metadata]
            reader_generator = self._object_target_reader.fetch(
                self._transfer_chunk_size_bytes)
            async for _ in reader_generator:
                pass

            source_content_length = self._object_source_reader.get_content_length()
            target_content_length = self._object_target_reader.get_content_length()

            _logger.info(
                "Content Length : Source {} and Target {}".format(
                    source_content_length,
                    target_content_length))

            if source_content_length == target_content_length:
                _logger.info(
                    "Content length matched for job_id {}".format(
                        self._job_id))
            else:
                _logger.error(
                    "Content length not matched for job_id {}".format(
                        self._job_id))

    def pause(self):
        """Pause the running object tranfer."""
        pass  # XXX

    def resume(self):
        """Resume the running object tranfer."""
        pass  # XXX

    def abort(self):
        """Abort the running object tranfer."""
        self._object_writer.abort()
