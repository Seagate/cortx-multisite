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

import asyncio
from collections import OrderedDict
from .job import Job
from .job import JobState
from .job import JobJsonEncoder
from .s3_common import move_across_sets
import json


class Jobs:
    @staticmethod
    def dumps(obj):
        """Helper to format json."""
        return json.dumps(obj._jobs, cls=JobJsonEncoder)

    @staticmethod
    def list_dumps(obj):
        return json.dumps(obj, cls=JobJsonEncoder)

    def __init__(self, logger, label, timeout=None):
        """
        Initialises collection with given label used for logging. Entries in
        Collection will be retained for given timeout. When timeout is
        not specified, entries will remain until explicitly removed.
        Args:
            logger (logger): For debug logging.
            label (str): Identifies the collection in logs.
            timeout (int, optional): Specified in secs. Defaults to None.
        """
        # Dictionary holding replication_id and replication record.
        # e.g. : jobs = {"replication-id": Job({"attribute-1": "foo"})}
        self._jobs = {}
        self._logger = logger
        self._label = label
        self._timeout = timeout

        # Additionally store job_id and replication_id mapping.
        self._job_id_to_replication_id_map = {}

        # Set of replication-id per Job state.
        # For faster lookups as per state.
        # _jobs = _jobs_queued + _jobs_inprogress + _jobs_completed
        self._jobs_queued = OrderedDict()
        self._jobs_inprogress = set()
        self._jobs_paused = set()
        self._jobs_completed = set()

    def get_keys(self):
        """Returns all jobs."""
        return self._jobs.keys()

    def reset(self):
        """Clear all jobs."""
        self._jobs.clear()
        self._jobs_queued.clear()
        self._jobs_inprogress.clear()
        self._jobs_paused.clear()
        self._jobs_completed.clear()

    def get_queued(self, count=None):
        """Get list of queued jobs.

        Args:
            count (int, optional): Number if jobs to return. Defaults to None.
            When count is None, return all jobs.

        Returns
        -------
            list[Job]: List of jobs in queued state.
        """
        # Creates array reference, use cautiously w.r.t performance.
        queued_list = []
        if count is None:
            # Return all.
            count = len(self._jobs_queued)

        # Only return first 'count' number of entries.
        for replication_id in self._jobs_queued.keys():
            if count == 0:
                break
            count -= 1
            queued_list.append(
                self.get_job(replication_id))

        return queued_list

    def get_inprogress(self):
        """Get list of inprogress jobs."""
        # Creates new dictionary reference, use cautiously w.r.t performance.
        in_progress_list = [self._jobs for key in self._jobs_inprogress]
        return in_progress_list

    def get_paused(self):
        """Get list of paused jobs."""
        # Creates new dictionary reference, use cautiously w.r.t performance.
        paused_list = [self._jobs for key in self._jobs_paused]
        return paused_list

    def get_completed(self):
        """Get list of completed jobs."""
        # Creates new dictionary reference, use cautiously w.r.t performance.
        completed_list = [self._jobs for key in self._jobs_completed]
        return completed_list

    def move_to_inprogress(self, replication_id):
        """Move job to in-progress list."""
        if replication_id in self._jobs_queued:
            self._logger.debug(
                "State change [Queued to Inprogress] for replication-id {},".
                format(replication_id))

            self._jobs_queued.pop(replication_id)
            self._jobs_inprogress.add(replication_id)
        elif replication_id in self._jobs_paused:
            self._logger.debug(
                "State change [Paused to Inprogress] for replication-id {},".
                format(replication_id))
            move_across_sets(self._jobs_paused, self._jobs_inprogress,
                             replication_id)
        else:
            # If was not in queued/paused, then invalid state.
            assert False, "Bug: Invalid state transition for job {}".format(
                replication_id
            )

    def move_to_pause(self, replication_id):
        """Move job to paused list."""
        if replication_id in self._jobs_inprogress:
            self._logger.debug(
                "State change [Inprogress to Paused] for replication-id {},".
                format(replication_id))
            move_across_sets(self._jobs_inprogress, self._jobs_paused,
                             replication_id)
        else:
            # If was not in inprogress, then invalid state.
            assert False, "Bug: Invalid state transition for job {}".format(
                replication_id
            )

    def move_to_queued(self, replication_id):
        """Move job to queued list."""
        if replication_id in self._jobs_inprogress:
            self._logger.debug(
                "State change [Inprogress to Queued] for replication-id {},".
                format(replication_id))
            self._jobs_queued[replication_id] = None
            self._jobs_inprogress.remove(replication_id)
        else:
            # If was not in inprogress, then invalid state.
            assert False, "Bug: Invalid state transition for job {}".format(
                replication_id
            )

    def move_to_complete(self, replication_id):
        """Move job to paused list."""
        if replication_id in self._jobs_inprogress:
            self._logger.debug(
                "State change [Inprogress to Complete]" +
                " for replication-id {},".format(replication_id))
            move_across_sets(self._jobs_inprogress, self._jobs_completed,
                             replication_id)
        else:
            # If was not in inprogress, then invalid state.
            assert False, "Bug: Invalid state transition for job {}".format(
                replication_id
            )

    def count(self):
        """
        Returns total jobs in collection.

        Returns:
            int: Count of jobs in collection.
        """
        return len(self._jobs)

    def queued_count(self):
        """
        Returns total jobs count in queued state.

        Returns:
            int: Count of queued jobs in collection.
        """
        return len(self._jobs_queued)

    def inprogress_count(self):
        """
        Returns in-progress jobs count in collection.

        Returns:
            int: Count of in-progress jobs in collection.
        """
        return len(self._jobs_inprogress)

    def completed_count(self):
        """
        Returns completed jobs count in collection.

        Returns:
            int: Count of completed jobs in collection.
        """
        return len(self._jobs_completed)

    def is_job_present(self, replication_id):
        """
        Checks if given replication id is present.

        Args:
            replication_id (str): Replication identifier.
        """
        if replication_id in self._jobs:
            return True
        return False

    def add_job_using_json(self, job_json):
        """
        Validate json, create and add job to job list.

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
        """
        Add job to job list.

        Args:
            job (Job): Job to be inserted in list.

        Returns:
            [bool]: True if successfully added, else false if already exists.
        """
        if self.is_job_present(job.get_replication_id()):
            return False
        self._logger.debug("Jobs[{}]: Adding job with job_id {}.".
                           format(self._label, job.get_job_id()))
        # Job not present add it and return success=True
        self._jobs[job.get_replication_id()] = job
        self._job_id_to_replication_id_map[job.get_job_id()] = \
            job.get_replication_id()
        # Initial state is queued.
        self._jobs_queued[job.get_replication_id()] = None

        if self._timeout is not None:
            asyncio.ensure_future(
                self.schedule_clear_cache(job.get_job_id())
            )
        return True

    def get_job(self, replication_id):
        """
        Search jobs list and return job with replication_id.

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
        """
        Find a job for given job id.

        Args:
            job_id (str): Job ID generated locally
        """
        replication_id = self._job_id_to_replication_id_map.get(job_id)
        if replication_id is None:
            return None
        return self.get_job(replication_id)

    def _remove_job(self, replication_id):
        """
        Removes a given job from collection and returns a reference.
        to removed Job entry.

        Args:
            replication_id (str): Job identifier.

        Returns:
            Job: Removed job record, None if job not present.
        """
        job = self._jobs.pop(replication_id, None)
        if job is not None:
            if job.get_state() == JobState.INITIAL:
                self._jobs_queued.pop(replication_id)
            elif job.get_state() == JobState.RUNNING:
                self._jobs_inprogress.remove(replication_id)
            elif job.get_state() == JobState.PAUSED:
                self._jobs_paused.remove(replication_id)
            else:
                # COMPLETED/ABORTED/FAILED.
                self._jobs_completed.remove(replication_id)

        return job

    def remove_job_by_job_id(self, job_id):
        """
        Remove a job for given job id.

        Args:
            job_id (str): Job ID generated locally
        """
        replication_id = self._job_id_to_replication_id_map.pop(job_id, None)
        if replication_id is None:
            return None
        self._logger.debug("Jobs[{}]: Removing job with job_id {}.".
                           format(self._label, job_id))
        return self._remove_job(replication_id)

    async def schedule_clear_cache(self, job_id):
        """
        Clear entry from collection after given timeout.

        Args:
            job_id (str): Job to clear.
            timeout (int): 0 Dont clear, else clear after timeout secs.
        """
        if self._timeout is not None:
            self._logger.debug(
                "Jobs[{}]: Schedule job_id [{}] to be expired after {} secs".
                format(self._label, job_id, self._timeout))
            await asyncio.sleep(self._timeout)
            self._logger.debug(
                "Jobs[{}]: job_id [{}] entry expired.".
                format(self._label, job_id))
            self.remove_job_by_job_id(job_id)
