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

from .job import Job
from .job import JobJsonEncoder
import json


class Jobs:
    def dumps(obj):
        """json """
        return json.dumps(obj._jobs, cls=JobJsonEncoder)

    def __init__(self):
        """Initialise jobs collection"""
        # Dictionary holding replication_id and replication record
        # e.g. : jobs = {"replication-id": Job({"attribute-1": "foo"})}
        self._jobs = {}

        # Additionally store job_id and replication_id mapping
        self._job_id_to_replication_id_map = {}

    def to_json(self):
        """Converts to json."""
        return Jobs.to_json(self)

    def get_keys(self):
        """Returns all jobs"""
        return self._jobs.keys()

    def reset(self):
        """Clear all jobs"""
        self._jobs.clear()

    def count(self):
        """Returns total jobs in collection.

        Returns:
            int: Count of jobs in collection.
        """
        return len(self._jobs)

    def add_jobs(self, jobs_dict):
        """Populate _jobs dict with multiple job entries"""
        self._jobs.update(jobs_dict)

    def is_job_present(self, replication_id):
        """Checks if given replication id is present.

        Args:
            replication_id (str): Replication identifier.
        """
        if replication_id in self._jobs:
            return True
        return False

    def add_job_using_json(self, job_json):
        """Validate json, create and add job to job list.

        Args:
            job_json (json): Job json record to be inserted in list.

        Returns:
            [job]: JOb if successfully added, else None if already exists.
        """
        job = Job(job_json)
        if self.add_job(job):
            return job
        return None

    def add_job(self, job):
        """Add job to job list.

        Args:
            job (Job): Job to be inserted in list.

        Returns:
            [bool]: True if successfully added, else false if already exists.
        """
        if self.is_job_present(job.get_replication_id()):
            return False
        # Job not present add it and return success=True
        self._jobs[job.get_replication_id()] = job
        self._job_id_to_replication_id_map[job.get_job_id()] = \
            job.get_replication_id()
        return True

    def get_job(self, replication_id):
        """Search jobs list and return job with replication_id.
        Args:
            replication_id (str): Job identifier.
        Returns:
            [Job]: Job instance for give id.
        """
        job = None
        if replication_id in self._jobs:
            job = self._jobs[replication_id]
        return job

    def get_job_by_job_id(self, job_id):
        """Find a job for given job id.
        Args:
            job_id (str): Job ID generated locally
        """
        replication_id = self._job_id_to_replication_id_map.get(job_id)
        if replication_id is None:
            return None
        return self.get_job(replication_id)

    def remove_jobs(self, nr_entry):
        """
        Remove number of jobs and return the removed items.
        """
        if nr_entry < self.count():
            rm_count = nr_entry
        else:
            rm_count = self.count()

        # Fetch first rm_count entires to return
        ret_entries = dict(list(self._jobs.items())[0:rm_count])

        # Update _jobs collection after removing entries
        self._jobs = dict(list(self._jobs.items())[rm_count:])

        return ret_entries

    def _remove_job(self, replication_id):
        """Removes a given job from collection and returns a reference.
        to removed Job entry.

        Args:
            replication_id (str): Job identifier.

        Returns:
            Job: Removed job record, None if job not present.
        """
        return self._jobs.pop(replication_id, None)

    def remove_job_by_job_id(self, job_id):
        """Remove a job for given job id.

        Args:
            job_id (str): Job ID generated locally
        """
        replication_id = self._job_id_to_replication_id_map.pop(job_id)
        if replication_id is None:
            return None
        return self._remove_job(replication_id)
