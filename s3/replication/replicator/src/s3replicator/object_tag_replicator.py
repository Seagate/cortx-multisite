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
from s3replicationcommon.s3_get_object import S3AsyncGetObjectTagging
from s3replicationcommon.s3_put_object import S3AsyncPutObjectTagging
from s3replicationcommon.timer import Timer

_logger = logging.getLogger('s3replicator')


class ObjectTagReplicator:
    def __init__(self, job, transfer_chunk_size_bytes, source_session,
                 target_session) -> None:
        """Initialise."""
        self._transfer_chunk_size_bytes = transfer_chunk_size_bytes
        self._job_id = job.get_job_id()
        self._request_id = self._job_id
        self._timer = Timer()
        self._tag = {} #XXX
        self._s3_source_session = source_session

        self._object_tag_reader = S3AsyncGetObjectTagging(
            self._s3_source_session,
            self._request_id,
            job.get_source_bucket_name(),
            job.get_source_object_name())

        # Setup target site info
        self._s3_target_session = target_session

        self._object_tag_writer = S3AsyncPutObjectTagging(
            self._s3_target_session,
            self._request_id,
            job.get_target_bucket_name(),
            job.get_source_object_name(),
            tag_name, tag_value)

    def get_execution_time(self):
        """Return total time for Object replication."""
        return self._timer.elapsed_time_ms()

    async def start(self):
        # Start transfer
        self._timer.start()
        await self._object_tag_reader.fetch()
        self._timer.stop()
        _logger.info(
            "Tag read completed in {}ms for job_id {}".format(
                self._timer.elapsed_time_ms(), self._job_id))
        self._tags = self._object_tag_reader._get_tags_dict()

        print ("My tags are : {}".format(self._tags))

        self._timer.start()
        await self._object_tag_writer.send()
        _logger.info(
            "Replication of tag completed in {}ms for job_id {}".format(
                self._timer.elapsed_time_ms(), self._job_id))
        ## notify job state events
        #for label, observer in self._observers.items():
        #    _logger.debug(
        #        "Notify completion to observer with label[{}]".format(label))
        #    if self._object_tag_writer.get_state() == S3RequestState.PAUSED:
        #        await observer.notify(JobEvents.STOPPED, self._job_id)
        #    elif self._object_tag_writer.get_state() == S3RequestState.ABORTED:
        #        await observer.notify(JobEvents.ABORTED, self._job_id)
        #    else:
        #        await observer.notify(JobEvents.COMPLETED, self._job_id)

    def pause(self):
        """Pause the running object tranfer."""
        pass  # XXX

    def resume(self):
        """Resume the running object tranfer."""
        pass  # XXX

    def abort(self):
        """Abort the running object tranfer."""
        self._object_tag_writer.abort()
