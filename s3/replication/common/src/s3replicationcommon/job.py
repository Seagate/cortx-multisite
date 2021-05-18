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


# Job model to be used across both replication manager and replicator
class Job:
    """A Job class to store replication job attributes.
       Provides methods to serialise/deserialise as json."""

    def __init__(self, obj):
        """Initialise Job."""
        if obj is not None:
            self._obj = obj
        else:
            self._obj = {}

    def get_dict(self):
        return self._obj

    def from_json(self, json_string):
        """Loads Job attributes from json."""
        self._obj = json.loads(json_string)

    def to_json(self):
        """Converts Job to json."""
        return json.dumps(self._obj)

    def load_from_s3metadata(self, s3_md_json):
        """Loads Job attributes from S3 metadata json entry."""
        s3_md = json.loads(s3_md_json)
        # TBD Only capture interesting attributes, for now use as is.
        self._obj = s3_md

    def get_job_id(self):
        """Returns job id"""
        # XXX generate job id format.
        return self.get_src_object_name()

    def get_src_object_name(self):
        """Returns source object name"""
        return self._obj["Object-Name"]


class JobJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Job):
            return obj._obj
        return super().default(obj)
