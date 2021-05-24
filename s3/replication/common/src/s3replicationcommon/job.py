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

import json
import uuid
from enum import Enum


class ReplicationJobType:
    OBJECT_REPLICATION = "replicate_object"
    OBJECT_TAGS_REPLICATION = "replicate_object_tags"
    OBJECT_ACL_REPLICATION = "replicate_object_acl"  # Currently not supported.


class ReplicationJobRecordKey:
    ID = "replication-id"
    CREATE_TIME = "replication-event-create-time"


# Following job events can be observed by job observers.
class JobEvents(Enum):
    UNKNOWN = 1
    STARTED = 2  # start or resume
    STOPPED = 4  # pause
    COMPLETED = 5  # after successful/failed processing
    ABORTED = 6  # explicitly aborted

# Job model to be used across both replication manager and replicator


class Job:
    """
    A Job class to store replication job attributes. Provides methods to
    serialise/deserialise as json. Maintains S3 replication source and
    target details, operation type etc. For Job json format see sample in
    ../formats/replication_job.json
    """

    def __init__(self, obj):
        """Initialise Job."""
        if obj is not None:
            self._obj = obj
        else:
            self._obj = {}
        # There are 2 identifiers, job_id which is generated
        # and replication id that is sent by job creator.
        self._id = uuid.uuid4()
        self._replicator = None

    def set_replicator(self, replicator):
        """Sets a reference to replicator for future signals (pause/abort)"""
        self._replicator = replicator

    def pause(self):
        """Request replicator to pause"""
        self._replicator.pause()

    def resume(self):
        """Request replicator to resume"""
        self._replicator.resume()

    def abort(self):
        """Request replicator to abort"""
        self._replicator.abort()

    def get_dict(self):
        return self._obj

    def from_json(self, json_string):
        """Loads Job attributes from json."""
        self._obj = json.loads(json_string)
        self._replication_id = self._obj["replication-id"]

    def to_json(self):
        """Converts Job to json."""
        return json.dumps(self._obj)

    def get_replication_id(self):
        return self._obj["replication-id"]

    def get_job_id(self):
        """Returns job id"""
        return self._id

    def get_operation_type(self):
        """Get replication type"""
        return self._obj["source"]["operation"]["type"]

    # Source attribute accessors
    def get_source_bucket_name(self):
        """Returns source bucket name"""
        return self._obj["source"]["operation"]["attributes"]["Bucket-Name"]

    def get_source_object_name(self):
        """Returns source object name"""
        return self._obj["source"]["operation"]["attributes"]["Object-Name"]

    def get_source_object_size(self):
        return self._obj["source"]["operation"]["attributes"]["Content-Length"]

    def get_source_endpoint(self):
        return self._obj["source"]["endpoint"]

    def get_source_s3_service_name(self):
        return self._obj["source"]["service_name"]

    def get_source_s3_region(self):
        return self._obj["source"]["region"]

    def get_source_access_key(self):
        return self._obj["source"]["access_key"]

    def get_source_secret_key(self):
        return self._obj["source"]["secret_key"]

    # Target attribute accessors
    def get_target_bucket_name(self):
        """Returns target bucket name"""
        return self._obj["target"]["Bucket-Name"]

    def get_target_endpoint(self):
        return self._obj["target"]["endpoint"]

    def get_target_s3_service_name(self):
        return self._obj["source"]["service_name"]

    def get_target_s3_region(self):
        return self._obj["source"]["region"]

    def get_target_access_key(self):
        return self._obj["target"]["access_key"]

    def get_target_secret_key(self):
        return self._obj["target"]["secret_key"]


class JobJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Job):
            return obj._obj
        return super().default(obj)
