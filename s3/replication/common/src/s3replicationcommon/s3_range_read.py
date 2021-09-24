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
import sys
from s3replicationcommon.aws_v4_signer import AWSV4Signer
from s3replicationcommon.log import fmt_reqid_log
from s3replicationcommon.s3_common import S3RequestState
from s3replicationcommon.timer import Timer


class S3AsyncGetRangeRead:
    def __init__(self, session, request_id,
                 bucket_name, object_name,
                 object_range):
        """Initialise."""
        self._session = session
        # Request id for better logging.
        self._request_id = request_id
        self._logger = session.logger

        self._bucket_name = bucket_name
        self._object_name = object_name

        self._object_range = object_range

        self._remote_down = False
        self._http_status = None

        self._timer = Timer()
        self._state = S3RequestState.INITIALISED

    def get_state(self):
        """Returns current request state."""
        return self._state

    def get_execution_time(self):
        """Return total time for GET Object operation."""
        return self._timer.elapsed_time_ms()

    def get_etag(self):
        """Returns ETag for object."""
        return self._response_headers["ETag"].strip("\"")

    def get_content_range(self):
        """Get content range in bytes."""
        return self._response_headers["Content-Range"]

    # yields data chunk for given size
    async def fetch(self):
        request_uri = AWSV4Signer.fmt_s3_request_uri(
            self._bucket_name, self._object_name)

        query_params = ""
        body = ""
        obj_range = self._object_range

        headers = AWSV4Signer(
            self._session.endpoint,
            self._session.service_name,
            self._session.region,
            self._session.access_key,
            self._session.secret_key).prepare_signed_header(
            'GET',
            request_uri,
            query_params,
            body,
            obj_range)

        if (headers['Authorization'] is None):
            self._logger.error(fmt_reqid_log(self._request_id) +
                               "Failed to generate v4 signature")
            sys.exit(-1)

        self._logger.info(fmt_reqid_log(self._request_id) +
                          'GET on {}'.format(
                              self._session.endpoint + request_uri))
        self._logger.debug(fmt_reqid_log(self._request_id) +
                           "GET with headers {}".format(headers))
        self._timer.start()
        try:
            async with self._session.get_client_session().get(
                    self._session.endpoint + request_uri,
                    headers=headers) as resp:

                self._logger.info(fmt_reqid_log(self._request_id)
                                  + 'GET response received with'
                                  + ' status code: {}'.format(resp.status))
                self._logger.info('Response url {}'.format(
                    self._session.endpoint + request_uri))

                if resp.status == 206:
                    self._response_headers = resp.headers
                    self._logger.info('Response headers {}'.format(
                        self._response_headers))
                else:
                    self._state = S3RequestState.FAILED
                    self._logger.error(
                        fmt_reqid_log(self._request_id) +
                        'GET Object failed with http status: {}'.
                        format(resp.status) +
                        '\nError Response: Invalid object range')
                    return

                while True:
                    resp_data = await resp.content.read()
                    if not resp_data:
                        break
                    yield resp_data
                # end of While True

        except aiohttp.client_exceptions.ClientConnectorError as e:
            self._remote_down = True
            self._state = S3RequestState.FAILED
            self._logger.error(fmt_reqid_log(self._request_id) +
                               "Failed to connect to S3: " + str(e))
        self._timer.stop()
        return