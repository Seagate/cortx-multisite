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

import sys
import urllib
import xml.etree.ElementTree as ET
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

    def get_replicatin_priority(self):
        """Returns replication priority number."""
        return int(self._replication_priority)

    def get_replication_status(self):
        """Returns replication status."""
        return self._replication_status

    def get_replication_prefix(self):
        """Returns replication prefix used as a filter."""
        return self._replication_prefix

    def get_replication_dest_bucket(self):
        """Returns replication destination bucket name."""
        return self._replication_dest_bucket

    # yields data chunk for given size

    async def get(self):
        request_uri = AWSV4Signer.fmt_s3_request_uri(self._bucket_name)
        self._logger.debug(
            fmt_reqid_log(
                self._request_id) +
            "request_uri : {}".format(request_uri))
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

            self._logger.info(
                fmt_reqid_log(
                    self._request_id) +
                'GET on {}'.format(url))
            async with self._session.get_client_session().get(
                    url, params=query_params, headers=headers) as resp:
                self._logger.info(
                    fmt_reqid_log(
                        self._request_id) +
                    "Response url {}".format(
                        (resp.url)))
                self._logger.info(
                    fmt_reqid_log(
                        self._request_id) +
                    "Received response url {}".format(resp))

                if resp.status == 200:
                    self._logger.info(fmt_reqid_log(self._request_id) +
                                      "Received reponse [{} OK]".format(
                        resp.status))

                    # parse xml response and set all the bucket replication
                    # attributes for this object.
                    xml_resp = await resp.text()
                    response = ET.fromstring(xml_resp)

                    self._replication_rule = response[1].text
                    self._replication_id = response[0][0].text
                    self._replication_priority = response[0][1].text
                    self._replication_status = response[0][2].text
                    self._dlt_marker_replication_status = response[0][3][0].text
                    self._replication_prefix = response[0][4][0].text
                    self._replication_role = response[1].text

                    # Dest bucket is having fully querlified name
                    # e.g. arn::aws::s3:target-bucket-name. so strip only
                    # last token after splitting string using ':'.
                    self._replication_dest_bucket = (response[0][5][0].text).split(':')[-1]

                    # print all the replcation attributes
                    self._logger.info(
                        fmt_reqid_log(
                            self._request_id) +
                        'rule : {}'.format(
                            self._replication_rule))
                    self._logger.info(
                        fmt_reqid_log(
                            self._request_id) +
                        'id : {}'.format(
                            self._replication_id))
                    self._logger.info(
                        fmt_reqid_log(
                            self._request_id) +
                        'priority : {}'.format(
                            self._replication_priority))
                    self._logger.info(
                        fmt_reqid_log(
                            self._request_id) +
                        'status : {}'.format(
                            self._replication_status))
                    self._logger.info(
                        fmt_reqid_log(
                            self._request_id) +
                        'dlt_marker_status :{}'.format(
                            self._dlt_marker_replication_status))
                    self._logger.info(
                        fmt_reqid_log(
                            self._request_id) +
                        'prefix : {}'.format(
                            self._replication_prefix))
                    self._logger.info(
                        fmt_reqid_log(
                            self._request_id) +
                        'dest_bucket : {}'.format(
                            self._replication_dest_bucket))
                    self._logger.info(
                        fmt_reqid_log(
                            self._request_id) +
                        'role : {}'.format(
                            self._replication_role))

                else:
                    self._state = S3RequestState.FAILED
                    error_msg = await resp.text()
                    self._logger.error(
                        fmt_reqid_log(
                            self._request_id) +
                        'Error Response: {}'.format(error_msg))
        except Exception as e:
            self._logger.error(
                fmt_reqid_log(
                    self._request_id) +
                "Error: Exception '{}' occured!".format(e))

        self._timer.stop()
        self._logger.debug(fmt_reqid_log(self._request_id) +
                           "execution time is : {}".format(
            self.get_execution_time()))

        return
