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
import xmltodict
from s3replicationcommon.aws_v4_signer import AWSV4Signer
from s3replicationcommon.log import fmt_reqid_log
from s3replicationcommon.s3_common import S3RequestState
from s3replicationcommon.timer import Timer


class ReplicationRule:
    def __init__(self):
        """Instantiate the matched rule's attributes."""
        self._delete_marker_replication_status = None
        self._account_id = None
        self._dest_bucket = None
        self._encryption_replication_key_id = None
        self._replication_time_status = None
        self._prefix = None
        self._tag = None
        self._priority = None
        self._id = None
        self._replication_status = None

    def __str__(self):
        """Method to print object with attributes."""
        return "_delete_marker_replication_status : {}\n_account : {}\
                \n_dest_bucket : {}\n_encryption_replication_key_id : {}\
                \n_replication_time_status : {}\n_prefix : {}\n_tag : {}\
                \n_priority : {}\n_id : {}\n_replication_status : {}\n".format(
            self._delete_marker_replication_status,
            self._account_id, self._dest_bucket,
            self._encryption_replication_key_id,
            self._replication_time_status,
            self._prefix, self._tag,
            self._priority,
            self._id, self._replication_status)


class S3AsyncGetBucketReplication():
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

    def get_execution_time(self):
        """Return total time for GET Object operation."""
        return self._timer.elapsed_time_ms()

    @staticmethod
    def prepare_matched_rule_object(rule):
        """Initialise the attributes from matched rules."""
        policy_obj = ReplicationRule()

        if 'DeleteMarkerReplication' in rule:
            if 'Status' in rule['DeleteMarkerReplication']:
                policy_obj._delete_marker_replication_status = \
                    rule['DeleteMarkerReplication']['Status']
        if 'Destination' in rule:
            if 'Bucket' in rule['Destination']:
                policy_obj._dest_bucket = rule['Destination']['Bucket'].split(
                    ':')[-1]
            if 'EncryptionConfiguration' in rule['Destination']:
                policy_obj._encryption_replication_key_id = \
                    rule['Destination'][
                        'EncryptionConfiguration']['ReplicaKmsKeyID']
            if 'Account' in rule['Destination']:
                policy_obj._account_id = rule['Destination']['Account']
            if 'ReplicationTime' in rule['Destination']:
                policy_obj._replication_time_status = \
                    rule['Destination']['ReplicationTime']['Status']
        if 'Status' in rule:
            policy_obj._status = rule['Status']
        if 'Filter' in rule.keys():
            if 'Prefix' in rule['Filter'].keys():
                policy_obj._prefix = rule['Filter']['Prefix']
            if 'Tag' in rule['Filter'].keys():
                policy_obj._tag = rule['Filter']['Tag']
        if 'ID' in rule.keys():
            policy_obj._id = rule['ID']
        if 'Priority' in rule:
            policy_obj._priority = rule['Priority']
        return policy_obj

    def get_replication_rule(self, obj_name):
        """Returns matched replication rule for given bucket.

        Args
        ----
            [str]: object name to check against all prefixes
            in replication rules.

        Returns
        -------
            ReplicationRule type object: Matched rule if any, else None.

        """
        self._dest_bucket = None
        try:
            for key, value in (
                    self._response_dict['ReplicationConfiguration']).items():
                if key == 'Rule':
                    # Check if whether 'value' instance is list of rules
                    if isinstance(value, list):
                        # Iterate through different rules
                        for rule in value:
                            # Check if object name marches any rule prefix
                            if rule['Filter']['Prefix'] in obj_name:
                                return S3AsyncGetBucketReplication.prepare_matched_rule_object(
                                    rule)
                    # If only one rule is present
                    else:
                        if value['Filter']['Prefix'] in obj_name:
                            return self.prepare_matched_rule_object(
                                value)

        except Exception as e:
            self._logger.error(
                "Failed to get rule! Exception type : {}".format(e))

    async def get(self):
        """Yields data chunk for given size."""
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

        # Request url
        url = self._session.endpoint + request_uri

        self._logger.info(fmt_reqid_log(self._request_id) +
                          'GET on {}'.format(url))

        self._timer.start()

        try:

            async with self._session.get_client_session().get(
                    url, params=query_params, headers=headers) as resp:
                self._logger.debug(fmt_reqid_log(self._request_id) +
                                   "Response url {}".format(
                    (resp.url)))
                self._logger.debug(fmt_reqid_log(self._request_id) +
                                   "Received response url {}".format(resp))

                if resp.status == 200:
                    self._logger.info(fmt_reqid_log(self._request_id) +
                                      "Received reponse [{} OK]".format(
                        resp.status))

                    xml_resp = await resp.text()
                    self._response_dict = xmltodict.parse(xml_resp)

                    self._logger.debug(
                        'Response xml : {}\n'.format(
                            self._response_dict))

                else:
                    self._state = S3RequestState.FAILED
                    error_msg = await resp.text()
                    self._logger.error(fmt_reqid_log(self._request_id) +
                                       'Error Response: {}'.format(error_msg))
        except Exception as e:
            self._logger.error(fmt_reqid_log(self._request_id) +
                               "Error: Exception '{}' occured!".format(e))

        self._timer.stop()
        self._logger.debug(fmt_reqid_log(self._request_id) +
                           "execution time is : {}".format(
            self.get_execution_time()))

        return
