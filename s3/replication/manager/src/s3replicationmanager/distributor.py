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
import logging
from enum import Enum
from .replicator_client import ReplicatorClient


_logger = logging.getLogger("s3replicationmanager")


class DistributorState(Enum):
    INITIAL = 1
    RUNNING = 2  # start or resume
    PAUSED = 4  # pause
    STOPPED = 5  # gracefully stopped
    ABORTED = 6  # abort

    def __str__(self):
        """Helps stringify to name only."""
        return self.name


class JobDistributor:
    def __init__(self, app):
        """Initialise."""
        self._app = app
        self._polling_interval = app["config"].job_polling_interval
        self._state = DistributorState.INITIAL

    async def start(self):
        """Starts distributor loop for distributing jobs to subscribers."""
        self._state = DistributorState.RUNNING
        _logger.info("Job distributor loop started...")
        subscribers_list = self._app['subscribers']
        jobs_list = self._app['all_jobs']
        while self._state == DistributorState.RUNNING:
            # Wait for next interval.
            await asyncio.sleep(self._polling_interval)

            if self._state == DistributorState.RUNNING:
                # Scan jobs list and send to subscribers.
                _logger.debug("Checking jobs for distribution.")

                if len(subscribers_list) == 0:
                    _logger.debug("No subscribers registered.")
                    continue

                if jobs_list.queued_count() == 0:
                    _logger.debug("No jobs available to distribute.")
                    continue

                # For each subscriber, check count to send as per prefetch.
                task_list = []
                jobs_list_per_task = []  # so we can co-relate with task
                for subscriber_id, subscriber in subscribers_list.items():
                    _logger.debug("Processing subscriber id {}".format(
                        subscriber_id))
                    # How many more subscriber can accept?
                    capacity = subscriber.pending_capacity()

                    # Find count of jobs in pending jobs.
                    available_jobs_count = jobs_list.queued_count()

                    # Identify how many jobs to send to current subscriber.
                    count_to_send = 0
                    if available_jobs_count == 0:
                        # No available jobs, break for subscribers and wait
                        _logger.debug("No jobs available to distribute.")
                        break
                    elif capacity == 0:
                        # Current subscriber has no more capacity.
                        _logger.debug("Subscriber with id {} is busy.")
                        continue
                    elif available_jobs_count > capacity:
                        # Send capacity jobs.
                        count_to_send = capacity
                    else:
                        # We dont have enough to fullfill capacity, send all.
                        count_to_send = available_jobs_count

                    # Extract first count_to_send number of jobs from queue.
                    jobs_to_send = jobs_list.get_queued(count_to_send)
                    replicator_client = ReplicatorClient(subscriber)

                    # Schedule async job send using http POST.
                    task = asyncio.ensure_future(replicator_client.post(
                        jobs_to_send))
                    task_list.append(task)
                    jobs_list_per_task.append(jobs_to_send)

                    # Move jobs_to_send to inprogress list.
                    for job in jobs_to_send:
                        jobs_list.move_to_inprogress(job.get_replication_id())

                # end of for each subscriber

                post_jobs_response_list = await asyncio.gather(*task_list)

                # Process the job post responses.
                for client in post_jobs_response_list:
                    if client.http_status == 201:
                        # Job was posted successfully.
                        _logger.debug(
                            "Jobs posted successfully to subscriber id {}".
                            format(subscriber_id))
                    else:
                        # Job post failed, move back to queued.
                        _logger.debug(
                            "Failed to post jobs to subscriber id {}".
                            format(subscriber_id))

                        for job in client.jobs_to_send:
                            jobs_list.move_to_queued(job.get_replication_id())

            elif self._state == DistributorState.PAUSED:
                # If paused just loop and do nothing.
                _logger.debug("Job distributor is paused, do nothing.")
            else:
                # Either Stopped or aborted, break while loop.
                _logger.debug("Job distributor {}".str(self._state))
                break

    def stop(self):
        """Stops the Distributor loop."""
        _logger.debug("Stopping job distribution.")
        self._state = DistributorState.STOPPED

    def pause(self):
        """Pauses the Distributor loop."""
        _logger.debug("Pausing job distribution.")
        self._state = DistributorState.PAUSED

    def resume(self):
        """Resumes the Distributor loop."""
        _logger.debug("Resuming job distribution.")
        self._state = DistributorState.RUNNING

    def on_client_send_done(self, client):
        """Once client send completes, handle success or failure."""
        pass
