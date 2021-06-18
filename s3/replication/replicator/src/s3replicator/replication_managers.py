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
from collections import OrderedDict
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

    async def subscribe(self, self_endpoint, prefetch_count):
        """Subscribe to remote replication manager for jobs.

        Args
        -----
            self_endpoint (str): url for replicator (current process).
            prefetch_count (int): maximum count of jobs to receive from
            replication manager.

        Returns
        -------
            bool: True when subscribed successfully, False when failed.
        """

        subscriber_payload = subscribe_payload_template()

        subscriber_payload.pop("id")  # replication manager will generate.
        subscriber_payload["endpoint"] = self_endpoint
        subscriber_payload["prefetch_count"] = prefetch_count

        resource_url = url_with_resources(self.endpoint, ["subscribers"])

        _logger.info(fmt_reqid_log(self.id) +
                     "PUT on {}".format(resource_url))
        self._timer.start()
        try:
            async with self.client_session.post(
                    resource_url, json=subscriber_payload) as response:
                self._timer.stop()

                _logger.info(
                    fmt_reqid_log(self.id) +
                    'HTTP Response: Status: {}'.format(response.status))

                if response.status == 201:  # CREATED
                    # Subscribed successfully.
                    self._state = S3RequestState.COMPLETED

                    response_body = await response.json()
                    _logger.debug(
                        fmt_reqid_log(self.id) +
                        'HTTP Response: Body: {}'.format(response_body))

                    self.subscriber_id = response_body["id"]
                else:
                    # Failed to Subscribe.
                    self._state = S3RequestState.FAILED
                    _logger.error(fmt_reqid_log(self.id) +
                                  "Failed to Subscribe.")
        except aiohttp.client_exceptions.ClientConnectorError as e:
            self._timer.stop()
            self._state = S3RequestState.FAILED
            _logger.error(fmt_reqid_log(self.id) +
                          "Failed to connect to Replication Manager: " +
                          str(e))
        if self._state == S3RequestState.COMPLETED:
            return True
        else:
            return False


class ReplicationManagerJsonEncoder(json.JSONEncoder):
    def default(self, o):  # pylint: disable=E0202
        if isinstance(o, ReplicationManager):
            return o.get_dictionary()
        return super().default(o)


class ReplicationManagers(OrderedDict):
    @staticmethod
    def dumps(obj):
        """Helper to format json."""
        return json.dumps(obj, cls=ReplicationManagerJsonEncoder)

    def __init__(self):
        """Initialise ReplicationManagers collection."""
        # Dictionary holding manager_id and attributes
        # E.g. : manager =
        #     {'id':'some-uuid','endpoint':'http://localhost:8080'}
        # managers = {some-uuid': ReplicationManager(endpoint), ...}
        super(ReplicationManagers, self).__init__()

    async def close(self):
        """Resets and closes all replication manager sessions."""
        for id, manager in self.items():
            await manager.close()
