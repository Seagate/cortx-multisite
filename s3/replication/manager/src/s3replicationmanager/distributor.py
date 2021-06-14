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
        while self._state == DistributorState.RUNNING:
            # Wait for next interval.
            await asyncio.sleep(self._polling_interval)

            if self._state == DistributorState.RUNNING:
                # Scan jobs list and send to subscribers.
                _logger.debug("Sending jobs to subscribers.")

                # For each subscriber, check count to send as per prefetch.

                # Find count jobs in pending jobs.

                # Send count jobs to subscriber from what we have.

                pass
            elif self._state == DistributorState.PAUSED:
                # If paused just loop and do nothing.
                _logger.debug("Job distributor is paused, do nothing.")
                pass
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
