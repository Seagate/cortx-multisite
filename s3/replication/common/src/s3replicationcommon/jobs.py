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
        # Dictionary holding job_id and fdmi record
        # e.g. : jobs = {"job1": Job({"obj_name": "foo"})}
        self._jobs = {}

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
        """Returns total jobs in collection."""
        return len(self._jobs)

    def update_jobs(self, jobs_dict):
        """Populdate _jobs dict with another dictionary"""
        self._jobs.update(jobs_dict)

    def add_job_using_json(self, job_json):
        """Validate the job and add to the dictionary"""
        job = Job(job_json)
        self._jobs[job.get_job_id()] = job
        return job

    def add_job(self, job):
        """Adds job to the dictionary"""
        self._jobs[job.get_job_id()] = job

    def get_job(self, job_id):
        """Search jobs list and return job with job_id"""
        job = None
        if job_id in self._jobs:
            job = self._jobs[job_id]
        else:
            # Job with job_id not found.
            job = None
        return job

    def remove_jobs(self, nr_entry):
        """Remove number of jobs, return and update dict
        This function will compare nr_entry with available
        job count and will use count whichever is lesser
        to remove and return jobs and update the _jobs"""
        if nr_entry < self.count():
            rm_count = nr_entry
        else:
            rm_count = self.count()

        ret_entries = dict(list(self._jobs.items())[:rm_count])
        self._jobs = dict(list(self._jobs.items())[rm_count:])

        return ret_entries

    def remove_job(self, job_id):
        """Remove a job the dictionary and return remove Job entry"""
        job = None
        if job_id in self._jobs:
            job = self._jobs.pop(job_id)
        else:
            # Job with job_id not found.
            job = None
        return job
