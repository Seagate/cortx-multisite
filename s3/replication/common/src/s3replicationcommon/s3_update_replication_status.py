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
import json
import base64
from s3replicationcommon.s3_common import S3RequestState
from s3replicationcommon.timer import Timer
from s3replicationcommon.aws_v4_signer import AWSV4Signer
from s3replicationcommon.log import fmt_reqid_log


class S3AsyncUpdatereplicationStatus:
    def __init__(self, session, request_id,
                 bucket_name, object_name):
        """Initialise."""
        self._session = session
        # Request id for better logging.
        self._request_id = request_id
        self._logger = session.logger

        self._bucket_name = bucket_name
        self._object_name = object_name

        self.remote_down = False
        self._http_status = None

        self._timer = Timer()
        self._state = S3RequestState.INITIALISED

        self.global_bucket_index_id = "AAAAAAAAAHg=-AQAQAAAAAAA="
        self.bucket_metadata_index_id = "AAAAAAAAAHg=-AgAQAAAAAAA="

    def get_state(self):
        """Returns current request state."""
        return self._state

    def get_execution_time(self):
        """Return total time for HEAD Object operation."""
        return self._timer.elapsed_time_ms()

    def kv_session(self, index, key, value=None):
        request_uri = '/indexes/{}/{}'.format(index, key)
        full_uri = self._session.admin_endpoint + request_uri

        query_params = ""
        body = value or ""
        headers = AWSV4Signer(
            self._session.admin_endpoint,
            self._session.service_name,
            self._session.region,
            self._session.access_key,
            self._session.secret_key).prepare_signed_header(
            'GET' if value is None else 'PUT',
            request_uri,
            query_params,
            body
        )

        if (headers['Authorization'] is None):
            self._logger.error(fmt_reqid_log(self._request_id) +
                               "Failed to generate v4 signature")
            sys.exit(-1)

        self._logger.info(fmt_reqid_log(self._request_id) +
                          'Motr index operation on {} {}'.format(
                              full_uri, body))

        if value is None:
            return self._session.get_client_session().get(
                full_uri,
                params=query_params, headers=headers)
        else:
            return self._session.get_client_session().put(
                full_uri,
                params=query_params, headers=headers,
                data=body.encode())

    async def update(self, status):
        self._timer.start()
        self._state = S3RequestState.RUNNING

        try:
            if self._session.admin_endpoint is None:
                self._logger.warn(fmt_reqid_log(self._request_id)
                                  + 'Admin API not configured, '
                                  + 'skipping source metadata update')
                self._state = S3RequestState.COMPLETED
                return

            async with self.kv_session(
                    self.global_bucket_index_id,
                    self._bucket_name) as resp:

                if resp.status == 200:
                    bucket_info = json.loads(await resp.text())
                    self._logger.info(fmt_reqid_log(self._request_id) +
                                      'Bucket index lookup for {}'.
                                      format(self._bucket_name) +
                                      'response received with' +
                                      ' status code: {}'.
                                      format(resp.status))
                    self._logger.debug(
                        'bucket info: {}'.format(bucket_info))

                else:
                    self._state = S3RequestState.FAILED
                    error_msg = await resp.text()
                    self._logger.error(
                        fmt_reqid_log(self._request_id) +
                        'Index operation failed with http status: {}'.
                        format(resp.status) +
                        ' Error Response: {}'.format(error_msg))
                    return

            bucket_owner = bucket_info['account_id']

            async with self.kv_session(
                    self.bucket_metadata_index_id,
                    bucket_owner + '/' + self._bucket_name) as resp:

                if resp.status == 200:
                    bucket_metadata = json.loads(await resp.text())

                    self._logger.info(fmt_reqid_log(self._request_id) +
                                      'Bucket index lookup for {} response'.
                                      format(self._bucket_name) +
                                      ' received with status code: {}'.
                                      format(resp.status))
                    self._logger.debug(
                        'bucket metadata: {}'.format(bucket_metadata))

                else:
                    self._state = S3RequestState.FAILED
                    error_msg = await resp.text()
                    self._logger.error(
                        fmt_reqid_log(self._request_id) +
                        'Index operation failed with http status: {}'.
                        format(resp.status) +
                        ' Error Response: {}'.format(error_msg))
                    return

            layout = base64.b64decode(
                    bucket_metadata['motr_object_list_index_layout'])
            id_hi = base64.b64encode(layout[0:8]).decode()
            id_lo = base64.b64encode(layout[8:16]).decode()
            metadata_index = id_hi + '-' + id_lo

            async with self.kv_session(
                    metadata_index,
                    self._object_name) as resp:

                if resp.status == 200:
                    object_metadata = json.loads(await resp.text())
                    self._logger.info(fmt_reqid_log(self._request_id) +
                                      'Object index lookup for {} in {}'.
                                      format(self._object_name,
                                             metadata_index) +
                                      ' response received with' +
                                      ' status code: {}'.
                                      format(resp.status))
                    self._logger.debug(
                        'object metadata: {}'.format(object_metadata))

                else:
                    self._state = S3RequestState.FAILED
                    error_msg = await resp.text()
                    self._logger.error(
                        fmt_reqid_log(self._request_id) +
                        'Index operation failed with http status: {}'.
                        format(resp.status) +
                        ' Error Response: {}'.format(error_msg))
                    return

            object_metadata['x-amz-replication-status'] = status

            async with self.kv_session(
                    metadata_index,
                    self._object_name,
                    json.dumps(object_metadata)) as resp:

                if resp.status == 200:
                    self._logger.info(fmt_reqid_log(self._request_id) +
                                      'Set x-amz-replication-status for ' +
                                      '{} to {}, response received with'.
                                      format(self._object_name, status) +
                                      ' status code: {}'.
                                      format(resp.status))
                    self._logger.debug(
                        'updated object metadata: {}'.format(object_metadata))

                else:
                    self._state = S3RequestState.FAILED
                    error_msg = await resp.text()
                    self._logger.error(
                        fmt_reqid_log(self._request_id) +
                        'Index operation failed with http status: {}'.
                        format(resp.status) +
                        ' Error Response: {}'.format(error_msg))
                    return

            self._state = S3RequestState.COMPLETED

        except aiohttp.client_exceptions.ClientConnectorError as e:
            self.remote_down = True
            self._state = S3RequestState.FAILED
            self._logger.error(fmt_reqid_log(self._request_id) +
                               "Failed to connect to S3: " + str(e))
        finally:
            self._timer.stop()

    def pause(self):
        self._state = S3RequestState.PAUSED
        # XXX Take real pause action

    def resume(self):
        self._state = S3RequestState.PAUSED
        # XXX Take real resume action

    def abort(self):
        self._state = S3RequestState.ABORTED
        # XXX Take abort pause action
