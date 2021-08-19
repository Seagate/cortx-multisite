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


class S3AsyncGetBucketReplication:
    def __init__(self, session, request_id, bucket_name):
        """Initialise."""
        self._session = session
        # Request id for better logging.
        self._request_id = request_id
        self._logger = session.logger

        self._bucket_name = bucket_name

        self.remote_down = False
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

    # yields data chunk for given size
    async def get(self):

        request_uri = '/' + urllib.parse.quote(self._bucket_name, safe='')
        self._logger.debug ("request_uri : {}".format(request_uri))
        # Add bucket-replication policy query
        query_params = urllib.parse.urlencode({'replication': None})
        body = ""

        headers = AWSV4Signer(
            self._session.endpoint,
            self._session.service_name,
            self._session.region,
            self._session.access_key,
            self._session.secret_key).prepare_signed_header(
            'GET',
            request_uri,
            query_params,
            body)

        if (headers['Authorization'] is None):
            self._logger.error(fmt_reqid_log(self._request_id) +
                               "Failed to generate v4 signature")
            sys.exit(-1)

        self._timer.start()
        try:
            # Request url
            url = self._session.endpoint + request_uri

            self._logger.info('GET on {}'.format(url))
            async with self._session.get_client_session().get(url, params=query_params, headers=headers) as resp:
                self._logger.info("Response url {}".format((resp.url)))
                self._logger.info("Received response url {}".format(resp))

                if resp.status == 200:
                    self._logger.info("Received reponse [{} OK]".format(resp.status))

                    total_received = 0
                    while True:
                        chunk = await resp.content.read(1024)
                        if not chunk:
                            break
                        total_received += len(chunk)
                        self._logger.info("Received data {}".format(chunk))
                else:
                    self._state = S3RequestState.FAILED
                    error_msg = await resp.text()
                    self._logger.error('Error Response: {}'.format(error_msg))

        except:
            self._logger.error("Error: Exception occured!")

        self._timer.stop()
        self._logger.debug("execution time is : {}".format(self.get_execution_time()))

        return
