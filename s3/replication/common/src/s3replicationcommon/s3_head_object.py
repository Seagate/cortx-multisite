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
from s3replicationcommon.s3_common import S3RequestState
from s3replicationcommon.timer import Timer
from s3replicationcommon.aws_v4_signer import AWSV4Signer
from s3replicationcommon.log import fmt_reqid_log


class S3AsyncHeadObject:
    def __init__(self, session, request_id,
                 bucket_name, object_name,
                 version_id):
        """Initialise."""
        self._session = session
        # Request id for better logging.
        self._request_id = request_id
        self._logger = session.logger

        self._bucket_name = bucket_name
        self._object_name = object_name

        self._version_id = version_id

        self.remote_down = False
        self._http_status = None

        self._timer = Timer()
        self._state = S3RequestState.INITIALISED

    def get_accept_ranges(self):
        """Get range of bytes for object.

        Returns
        -------
            [str]: indicates that a range of bytes was specified for object.
        """
        self._resp_accept_range = self._response_headers.get(
            "Accept-Ranges", None)
        return self._resp_accept_range

    def get_cache_control(self):
        """Get caching behavior for object.

        Returns
        -------
            [str]: if set, returns cache policy
            and maximum age before expiring.
        """
        self._resp_cache_control = self._response_headers.get(
            "Cache-Control", None)
        return self._resp_cache_control

    def get_content_disposition(self):
        """Get presentational information for object.

        Returns
        -------
            [str]: attached filename/information for object.
        """
        self._resp_content_disposition = self._response_headers.get(
            "Content-Disposition", None)
        return self._resp_content_disposition

    def get_content_encoding(self):
        """Get content encodings for object.

        Returns
        -------
            [str]: specifies content encodings applied
            to object.
        """
        self._resp_content_encoding = self._response_headers.get(
            "Content-Encoding", None)
        return self._resp_content_encoding

    def get_content_language(self):
        """Get content language for object.

        Returns
        -------
            [str]: specify language the object content is in.
        """
        self._resp_content_lang = self._response_headers.get(
            "Content-Language", None)
        return self._resp_content_lang

    def get_content_length(self):
        """Get content length of object.

        Returns
        -------
            [int]: total content length of object.
        """
        self._resp_content_length = self._response_headers.get(
            "Content-Length", None)
        if self._resp_content_length is not None:
            self._resp_content_length = int(self._resp_content_length)
        return self._resp_content_length

    def get_content_type(self):
        """Get content type for object.

        Returns
        -------
            [str]: format of object data.
        """
        self._resp_content_type = self._response_headers.get(
            "Content-Type", None)
        return self._resp_content_type

    def get_etag(self):
        """Get etag for object.

        Returns
        -------
            [str]: opaque identifier.
        """
        self._resp_etag = self._response_headers.get("Etag", None)
        return self._resp_etag

    def get_expires(self):
        """Get date and time for object.

        Returns
        -------
            [str]: date and time at which the object is no longer cacheable.
        """
        self._resp_expires = self._response_headers.get("Expires", None)
        return self._resp_expires

    def get_last_modified(self):
        """Get last creation date of object.

        Returns
        -------
            [str]: date of the object.
        """
        self._resp_last_modified = self._response_headers.get(
            "Last-Modified", None)
        return self._resp_last_modified

    def get_server_name(self):
        """Get server name.

        Returns
        -------
            [str]: server name (SeagateS3 / AmazonS3).
        """
        self._resp_server_name = self._response_headers.get(
            "Server", None)
        return self._resp_server_name

    def get_x_amz_archive_status(self):
        """Get archive state of the object.

        Returns
        -------
            [str]: archieve state (ARCHIVE_ACCESS / DEEP_ARCHIVE_ACCESS)
        """
        self._resp_archive_status = self._response_headers.get(
            "x-amz-archive-status", None)
        return self._resp_archive_status

    def get_x_amz_delete_marker(self):
        """Get delete marker status for object.

        Returns
        -------
            [bool]: True if object retrived was a Delete Marker, else False.
        """
        self._resp_delete_marker = self._response_headers.get(
            "x-amz-delete-marker", None)
        if self._resp_delete_marker is not None:
            self._resp_delete_marker = bool(self._resp_delete_marker)
        return self._resp_delete_marker

    def get_x_amz_expiration(self):
        """Get expiration configuration of object.

        Returns
        -------
            [str]: expiry date and rule-id, if enabled.
        """
        self._resp_expiration = self._response_headers.get(
            "x-amz-expiration", None)
        return self._resp_expiration

    def get_x_amz_missing_meta(self):
        """Get missing metadata entries of object.

        Returns
        -------
            [int]: value of the number of unprintable metadata entries.
        """
        self._resp_missing_data = self._response_headers.get(
            "x-amz-missing-meta", None)
        if self._resp_missing_data is not None:
            self._resp_missing_data = int(self._resp_missing_data)
        return self._resp_missing_data

    def get_x_amz_mp_parts_count(self):
        """Get part counts of object.

        Returns
        -------
            [int]: total part count of an object.
        """
        self._resp_parts_count = self._response_headers.get(
            "x-amz-mp-parts-count", None)
        if self._resp_parts_count is not None:
            self._resp_parts_count = int(self._resp_parts_count)
        return self._resp_parts_count

    def get_x_amz_object_lock_legal_hold(self):
        """Get legal hold status value for the object.

        Returns
        -------
            [str]: ON if a legal hold is in effect for the object, else OFF.
        """
        self._resp_legal_hold = self._response_headers.get(
            "x-amz-object-lock-legal-hold", None)
        return self._resp_legal_hold

    def get_x_amz_object_lock_mode(self):
        """Get lock mode of object.

        Returns
        -------
            [str]: Valid response values - GOVERNANCE / COMPLIANCE.
        """
        self._resp_lock_mode = self._response_headers.get(
            "x-amz-object-lock-mode", None)
        return self._resp_lock_mode

    def get_x_amz_object_lock_retain_until_date(self):
        """Get date and time retention period expires of object.

        Returns
        -------
            [str]: date and time when retention period expires.
        """
        self._resp_lock_retention = self._response_headers.get(
            "x-amz-object-lock-retain-until-date", None)
        return self._resp_lock_retention

    def get_x_amz_replication_status(self):
        """Get replication status of object.

        Returns
        -------
            [str]: valid response values - PENDING, COMPLETED
            or FAILED indicating object replication status.
        """
        self._resp_replication_status = self._response_headers.get(
            "x-amz-replication-status", None)
        return self._resp_replication_status

    def get_x_amz_request_charged(self):
        """Get requester value of object.

        Returns
        -------
            [str]: Requester of an object.
        """
        self._resp_charged = self._response_headers.get(
            "x-amz-request-charged", None)
        return self._resp_charged

    def get_x_amz_request_id(self):
        """Get request id of object.

        Returns
        -------
            [str]: specific request id.
        """
        self._resp_id = self._response_headers.get(
            "x-amz-request-id", None)
        return self._resp_id

    def get_x_amz_restore(self):
        """Get the date when the restored copy expires.

        Returns
        -------
            [str]: ongoing-request and expiry-date of archived object.
        """
        self._resp_restore = self._response_headers.get("x-amz-restore", None)
        return self._resp_restore

    def get_x_amz_server_side_encryption(self):
        """Get aws kms or encryption key for object.

        Returns
        -------
            [str]: aws:kms if aws kms, else AES256.
        """
        self._resp_server_encryption = self._response_headers.get(
            "x-amz-server-side-encryption", None)
        return self._resp_server_encryption

    def get_x_amz_server_side_encryption_aws_kms_key_id(self):
        """Get aws kms id for object.

        Returns
        -------
            [str]: SSEKMSKeyId for object.
        """
        self._resp_srvenc_aws_kms = self._response_headers.get(
            "x-amz-server-side-encryption-aws-kms-key-id", None)
        return self._resp_srvenc_aws_kms

    def get_x_amz_server_side_encryption_bucket_key_enabled(self):
        """Get status of bucket key encryption for object.

        Returns
        -------
            [bool]: True if bucket key enabled, else False.
        """
        self._resp_srvenc_bucketkey = self._response_headers.get(
            "x-amz-server-side-encryption-bucket-key-enabled", None)
        if self._resp_srvenc_bucketkey is not None:
            self._resp_srvenc_bucketkey = bool(self._resp_srvenc_bucketkey)
        return self._resp_srvenc_bucketkey

    def get_x_amz_server_side_encryption_customer_algorithm(self):
        """Get encryption algorithm for object.

        Returns
        -------
            [str]: SSECustomerAlgorithm - encryption algorithm for object.
        """
        self._resp_srvenc_cust_algo = self._response_headers.get(
            "x-amz-server-side-encryption-customer-algorithm", None)
        return self._resp_srvenc_cust_algo

    def get_x_amz_server_side_encryption_customer_key_MD5(self):
        """Get encryption key for object.

        Returns
        -------
            [str]: SSECustomerKeyMD5 of object.
        """
        self._resp_srvenc_cust_key = self._response_headers.get(
            "x-amz-server-side-encryption-customer-key-MD5", None)
        return self._resp_srvenc_cust_key

    def get_x_amz_storage_class(self):
        """Get storage class of object.

        Returns
        -------
            [str]: storage class value of object.
        """
        self._resp_storage_class = self._response_headers.get(
            "x-amz-storage-class", None)
        return self._resp_storage_class

    def get_x_amz_version_id(self):
        """Get version id of object.

        Returns
        -------
            [str]: version id an object.
        """
        self._resp_version_id = self._response_headers.get(
            "x-amz-version-id", None)
        return self._resp_version_id

    def get_x_amz_website_redirect_location(self):
        """Get redirection website for object.

        Returns
        -------
            [str]: URL of redirect location.
        """
        self._resp_redirectlocation = self._response_headers.get(
            "x-amz-website-redirect-location", None)
        return self._resp_redirectlocation

    def get_state(self):
        """Returns current request state."""
        return self._state

    def get_execution_time(self):
        """Return total time for HEAD Object operation."""
        return self._timer.elapsed_time_ms()

    async def get(self, part_number):
        request_uri = AWSV4Signer.fmt_s3_request_uri(
            self._bucket_name, self._object_name)

        self._part_number = part_number

        query_params = urllib.parse.urlencode(
            {'partNumber': self._part_number, 'versionId': self._version_id})
        body = ""
        headers = AWSV4Signer(
            self._session.endpoint,
            self._session.service_name,
            self._session.region,
            self._session.access_key,
            self._session.secret_key).prepare_signed_header(
            'HEAD',
            request_uri,
            query_params,
            body
        )

        if (headers['Authorization'] is None):
            self._logger.error(fmt_reqid_log(self._request_id) +
                               "Failed to generate v4 signature")
            sys.exit(-1)

        self._logger.info(fmt_reqid_log(self._request_id) +
                          'HEAD on {}'.format(
                              self._session.endpoint + request_uri))
        self._logger.debug(fmt_reqid_log(self._request_id) +
                           "HEAD Request Header {}".format(headers))

        self._timer.start()
        try:
            async with self._session.get_client_session().head(
                    self._session.endpoint + request_uri,
                    params=query_params, headers=headers) as resp:

                if resp.status == 200:
                    self._response_headers = dict(resp.headers)
                    self._logger.info(fmt_reqid_log(self._request_id)
                                      + 'HEAD Object response received with'
                                      + ' status code: {}'.format(resp.status))
                    self._logger.info(
                        'received reponse header {}'.format(
                            self._response_headers))

                else:
                    self._state = S3RequestState.FAILED
                    error_msg = await resp.text()
                    self._logger.error(
                        fmt_reqid_log(self._request_id) +
                        'HEAD Object failed with http status: {}'.
                        format(resp.status) +
                        ' Error Response: {}'.format(error_msg))
                    return

                self._state = S3RequestState.RUNNING

        except aiohttp.client_exceptions.ClientConnectorError as e:
            self.remote_down = True
            self._state = S3RequestState.FAILED
            self._logger.error(fmt_reqid_log(self._request_id) +
                               "Failed to connect to S3: " + str(e))
        self._timer.stop()
        return

    def pause(self):
        self._state = S3RequestState.PAUSED
        # XXX Take real pause action

    def resume(self):
        self._state = S3RequestState.PAUSED
        # XXX Take real resume action

    def abort(self):
        self._state = S3RequestState.ABORTED
        # XXX Take abort pause action
