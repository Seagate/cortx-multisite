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
import uuid
from s3replicationcommon.log import fmt_reqid_log
from s3replicationcommon.s3_common import S3RequestState
from s3replicationcommon.s3_common import url_with_resources
from s3replicationcommon.templates import subscribe_payload_template
from s3replicationcommon.timer import Timer

_logger = logging.getLogger('s3replicator')


class ReplicationManager:
    def __init__(self, manager_endpoint):
        """Initialise ReplicationManager object."""
        # Id generated locally.
        self.id = str(uuid.uuid4())
        self.endpoint = manager_endpoint
        # Id returned for remote replication manager after subscribe.
        self.subscriber_id = None
        self.client_session = aiohttp.ClientSession()

        self._timer = Timer()
        self._state = S3RequestState.INITIALISED

    async def close(self):
        await self.client_session.close()

    def get_dictionary(self):
        return {
            "id": self.id,
            "endpoint": self.endpoint,
            "subscriber_id": self.subscriber_id
        }

    async def subscribe(self, replicator_endpoint, prefetch_count):
        """Subscribe to remote replication manager for jobs.

        Args
        -----
            replicator_endpoint (str): url for replicator (current process).
            prefetch_count (int): maximum count of jobs to receive from
            replication manager.

        Returns
        -------
            bool: True when subscribed successfully, False when failed.
        """
        subscriber_payload = subscribe_payload_template()

        subscriber_payload.pop("id")  # replication manager will generate.
        subscriber_payload["endpoint"] = replicator_endpoint
        subscriber_payload["prefetch_count"] = prefetch_count

        resource_url = url_with_resources(self.endpoint, ["subscribers"])
        req_id = str(uuid.uuid4())
        _logger.info(fmt_reqid_log(req_id) +
                     "PUT on {}".format(resource_url))
        self._timer.start()
        try:
            self._state = S3RequestState.RUNNING
            async with self.client_session.post(
                    resource_url, json=subscriber_payload) as response:
                self._timer.stop()

                _logger.info(
                    fmt_reqid_log(req_id) +
                    'HTTP Response: Status: {}'.format(response.status))

                if response.status == 201:  # CREATED
                    # Subscribed successfully.
                    self._state = S3RequestState.COMPLETED

                    response_body = await response.json()
                    _logger.debug(
                        fmt_reqid_log(req_id) +
                        'HTTP Response: Body: {}'.format(response_body))

                    self.subscriber_id = response_body["id"]
                else:
                    # Failed to Subscribe.
                    self._state = S3RequestState.FAILED
                    _logger.error(fmt_reqid_log(req_id) +
                                  "Failed to Subscribe.")
        except aiohttp.client_exceptions.ClientConnectorError as e:
            self._timer.stop()
            self._state = S3RequestState.FAILED
            _logger.error(fmt_reqid_log(req_id) +
                          "Failed to connect to Replication Manager: " +
                          str(e))
        if self._state == S3RequestState.COMPLETED:
            return True
        else:
            return False

    # Post the job status update to replicator.
    async def send_update(self, job_id, status):
        """Updates replication manager with job status.

        Args
        -----
            job_id (str): Job ID at the replication manager.
            status (str): completed/failed/aborted.

        Returns
        -------
            bool: True when status updated successfully, False when failed.
        """
        headers = {"Content-Type": "application/json"}
        payload = {"status": status}

        resource_url = url_with_resources(
            self.endpoint, ["jobs", job_id])
        req_id = str(uuid.uuid4())

        _logger.info(fmt_reqid_log(req_id) + 'PUT on {}'.format(resource_url))
        _logger.debug(fmt_reqid_log(req_id) +
                      "PUT with headers {}".format(headers))
        _logger.debug(fmt_reqid_log(req_id) + "PUT content {}".format(payload))

        self._timer.start()
        try:
            self._state = S3RequestState.RUNNING
            async with self.client_session.put(resource_url, headers=headers,
                                               json=payload) as resp:
                self._timer.stop()

                self._response_headers = resp.headers

                self.http_status = resp.status
                self.response = await resp.json()

                _logger.info(fmt_reqid_log(req_id) +
                             'PUT on {} returned http status: {}'.
                             format(resource_url, resp.status))

                if resp.status == 200:
                    self._state = S3RequestState.COMPLETED
                    _logger.info(fmt_reqid_log(req_id) +
                                 'PUT on {} returned Response: {}'.
                                 format(resource_url, self.response))
                else:
                    self._state = S3RequestState.FAILED
                    _logger.error(fmt_reqid_log(req_id) +
                                  'PUT on {} returned Response: {}'.
                                  format(resource_url, self.response))

        except aiohttp.client_exceptions.ClientConnectorError as e:
            self._timer.stop()
            self._state = S3RequestState.FAILED
            self.remote_down = True
            _logger.error(
                'Failed to connect to Replication manager: ' + str(e))

        if self._state == S3RequestState.COMPLETED:
            return True
        else:
            return False


class ReplicationManagerJsonEncoder(json.JSONEncoder):
    def default(self, o):  # pylint: disable=E0202
        if isinstance(o, ReplicationManager):
            return o.get_dictionary()
        return super().default(o)
