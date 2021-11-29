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
import urllib
from s3replicationcommon.aws_v4_signer import AWSV4Signer
from s3replicationcommon.log import fmt_reqid_log
from s3replicationcommon.s3_common import S3RequestState
from s3replicationcommon.timer import Timer


class S3AsyncUploadPart:
    def __init__(self, session, request_id,
                 bucket_name, object_name,
                 upload_id):
        """Initialise."""
        self._session = session
        # Request id for better logging.
        self._request_id = request_id
        self._logger = session.logger

        self._bucket_name = bucket_name
        self._object_name = object_name

        self._upload_id = upload_id

        self.remote_down = False
        self._http_status = None

        self._etag_dict = {}
        self._timer = Timer()
        self._state = S3RequestState.INITIALISED

    def get_state(self):
        """Returns current request state."""
        return self._state

    def get_response_header(self, header_key):
        """Returns response http header value."""
        if self._state == S3RequestState.COMPLETED:
            return self._response_headers[header_key]
        return None

    def get_execution_time(self):
        """Return total time for PUT Object operation."""
        return self._timer.elapsed_time_ms()

    def get_etag(self):
        """Returns ETag for object."""
        return self._response_headers["ETag"].strip("\"")

    def get_etag_dict(self):
        """Returns Etag dictionary."""
        return self._etag_dict

    # data_reader is object with fetch method that can yield data
    async def upload(self, data_reader, part_no, chunk_size):
        self._state = S3RequestState.RUNNING
        self._part_no = part_no

        request_uri = AWSV4Signer.fmt_s3_request_uri(
            self._bucket_name, self._object_name)

        print("Part Number : {}".format(self._part_no))
        query_params = urllib.parse.urlencode(
            {'partNumber': self._part_no, 'uploadId': self._upload_id})
        body = ""

        headers = AWSV4Signer(
            self._session.endpoint,
            self._session.service_name,
            self._session.region,
            self._session.access_key,
            self._session.secret_key).prepare_signed_header(
            'PUT',
            request_uri,
            query_params,
            body)

        if (headers['Authorization'] is None):
            self._logger.error(fmt_reqid_log(self._request_id) +
                               "Failed to generate v4 signature")
            sys.exit(-1)

        headers["Content-Length"] = str(chunk_size)

        self._logger.info(fmt_reqid_log(self._request_id) +
                          "PUT on {}".format(
                              self._session.endpoint + request_uri))
        self._logger.debug(fmt_reqid_log(self._request_id) +
                           "PUT with headers {}".format(headers))

        self._timer.start()
        try:
            async with self._session.get_client_session().put(
                    self._session.endpoint + request_uri,
                    headers=headers,
                    params=query_params,
                    data=data_reader.fetch(chunk_size)) as resp:
                self._timer.stop()

                self._http_status = resp.status
                self._response_headers = resp.headers

                self._logger.info(
                    fmt_reqid_log(self._request_id) +
                    'PUT Object completed with http status: {}'
                    '\n header{}'.format(
                        resp.status, self._response_headers))

                self._etag_dict[self._part_no] = self._response_headers["Etag"]

                if resp.status == 200:
                    self._state = S3RequestState.COMPLETED
                else:
                    error_msg = await resp.text()
                    self._logger.error(
                        fmt_reqid_log(self._request_id) +
                        'Error Response: {}'.format(error_msg))
                    self._state = S3RequestState.FAILED
        except aiohttp.client_exceptions.ClientConnectorError as e:
            self._timer.stop()
            self.remote_down = True
            self._state = S3RequestState.FAILED
            self._logger.error(fmt_reqid_log(self._request_id) +
                               "Failed to connect to S3: " + str(e))
        return
