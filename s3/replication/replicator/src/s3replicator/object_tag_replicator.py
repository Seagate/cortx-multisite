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
from s3replicationcommon.s3_get_object_tagging import S3AsyncGetObjectTagging
from s3replicationcommon.s3_put_object_tagging import S3AsyncPutObjectTagging
from s3replicationcommon.timer import Timer

_logger = logging.getLogger('s3replicator')


class ObjectTagReplicator:
    def __init__(self, job, source_session,
                 target_session) -> None:
        """Initialise."""
        self._job_id = job.get_job_id()
        self._request_id = self._job_id
        self._timer = Timer()
        self._tagset = job.get_object_tagset()
        self._s3_source_session = source_session

        self._source_bucket = job.get_source_bucket_name()
        self._source_object = job.get_source_object_name()

        # A set of observers to watch for varius notifications.
        # To start with job completed (success/failure)
        self._observers = {}

        # Setup target site info
        self._s3_target_session = target_session

        self._target_bucket = job.get_target_bucket_name()
        self._target_object = job.get_source_object_name()

    def get_execution_time(self):
        """Return total time for Object replication."""
        return self._timer.elapsed_time_ms()

    def setup_observers(self, label, observer):
        self._observers[label] = observer

    async def start(self):
        # Start transfer
        object_source_tag_reader = S3AsyncGetObjectTagging(
            self._s3_source_session,
            self._request_id,
            self._source_bucket,
            self._source_object)

        self._timer.start()
        await object_source_tag_reader.fetch()
        self._timer.stop()
        _logger.info(
            "Tag read completed in {}ms for job_id {}".format(
                self._timer.elapsed_time_ms(), self._job_id))
        self._tags = object_source_tag_reader.get_tags_dict()

        object_tag_writer = S3AsyncPutObjectTagging(
            self._s3_target_session,
            self._request_id,
            self._target_bucket,
            self._target_object,
            self._tags)

        self._timer.start()
        await object_tag_writer.send()
        _logger.info(
            "Replication of tag completed in {}ms for job_id {}".format(
                self._timer.elapsed_time_ms(), self._job_id))

        # notify job state events
        for label, observer in self._observers.items():
            _logger.debug(
                "Notify completion to observer with label[{}]".format(label))
            if object_tag_writer.get_state() == S3RequestState.PAUSED:
                await observer.notify(JobEvents.STOPPED, self._job_id)
            elif object_tag_writer.get_state() == S3RequestState.ABORTED:
                await observer.notify(JobEvents.ABORTED, self._job_id)
            else:
                await observer.notify(JobEvents.COMPLETED, self._job_id)

        if JobEvents.COMPLETED:
            # check object tags count of source and target objects
            # [user-defined metadata]
            object_target_tag_reader = S3AsyncGetObjectTagging(
                self._s3_target_session,
                self._request_id,
                self._target_bucket,
                self._target_object)

            await object_target_tag_reader.fetch()
            source_tags_count = object_source_tag_reader.get_tags_count()
            target_tags_count = object_target_tag_reader.get_tags_count()

            _logger.info(
                "Object tags count : Source {} and Target {}".format(
                    source_tags_count, target_tags_count))

            if source_tags_count == target_tags_count:
                _logger.info(
                    "Object tags count matched for job_id {}".format(
                        self._job_id))
            else:
                _logger.error(
                    "Object tags count not matched for job_id {}".format(
                        self._job_id))

    def pause(self):
        """Pause the running object tranfer."""
        pass  # XXX

    def resume(self):
        """Resume the running object tranfer."""
        pass  # XXX

    def abort(self):
        """Abort the running object tranfer."""
        self._object_tag_writer.abort()
