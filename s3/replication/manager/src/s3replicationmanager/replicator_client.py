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

import aiohttp
import json
import logging
from s3replicationcommon.s3_common import url_with_resources
from s3replicationcommon.timer import Timer
from s3replicationcommon.job import JobJsonEncoder

_logger = logging.getLogger("s3replicationmanager")


class ReplicatorClient:
    def __init__(self, subscriber):
        """Initialise."""
        self._subscriber = subscriber

        self.http_status = None
        self.response = None
        self.response_headers = None
        self.remote_down = False

        self._timer = Timer()

    def get_execution_time(self):
        """Return total time for PUT Object operation."""
        return self._timer.elapsed_time_ms()

    # Post the jobs to replicator.
    async def post(self, jobs_to_send):
        self.jobs_to_send = jobs_to_send

        headers = {"Content-Type": "application/json"}
        payload = json.dumps(jobs_to_send, cls=JobJsonEncoder)

        jobs_url = url_with_resources(self._subscriber.endpoint, ["jobs"])

        _logger.info('POST on {}'.format(jobs_url))
        _logger.debug('POST content {}'.format(payload))

        self._timer.start()
        try:
            async with self._subscriber.client_session.post(
                    jobs_url,
                    headers=headers,
                    data=payload) as resp:

                self._response_headers = resp.headers

                self.http_status = resp.status
                if resp.status == 201:
                    self.response = await resp.json()

                _logger.info(
                    'POST on {} completed with http status: {}'.format(
                        jobs_url, resp.status))
        except aiohttp.client_exceptions.ClientConnectorError as e:
            self.remote_down = True
            _logger.error('Failed to connect to replicator: ' + str(e))

        self._timer.stop()

        return self
