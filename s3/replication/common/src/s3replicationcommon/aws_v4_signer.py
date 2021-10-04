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
"""Utility class used for Authentication using V4 signature."""

import hmac
import hashlib
import urllib
import datetime


class AWSV4Signer(object):
    """Generate Authentication headers to validate requests."""

    def __init__(self, endpoint, service_name, region, access_key, secret_key):
        """Initialise config."""
        self._endpoint = endpoint
        self._service_name = service_name
        self._region = region
        self._access_key = access_key
        self._secret_key = secret_key

    # Helper method.
    def _get_headers(host, epoch_t, body_256hash):
        headers = {
            'host': host,
            'x-amz-content-sha256': body_256hash,
            'x-amz-date': AWSV4Signer._get_amz_timestamp(epoch_t)
        }
        return headers

    def _create_canonical_request(
            self,
            method,
            canonical_uri,
            canonical_query_string,
            body,
            epoch_t,
            host):
        """Create canonical request based on uri and query string."""
        body_256sha_hex = 'UNSIGNED-PAYLOAD'
        if body:
            # body has some content.
            body_256sha_hex = hashlib.sha256(body.encode('utf-8')).hexdigest()

        self._body_hash_hex = body_256sha_hex
        headers = AWSV4Signer._get_headers(host, epoch_t, body_256sha_hex)
        sorted_headers = sorted([k for k in headers])
        canonical_headers = ""
        for key in sorted_headers:
            canonical_headers += "{}:{}\n".format(
                key.lower(), headers[key].strip())

        signed_headers = "{}".format(";".join(sorted_headers))
        canonical_request = method + '\n' + canonical_uri + '\n' + \
            canonical_query_string + '\n' + canonical_headers + '\n' + \
            signed_headers + '\n' + body_256sha_hex
        return canonical_request

    # Helper method.
    def _sign(key, msg):
        """Return hmac value based on key and msg."""
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    # Helper method.
    def _getV4SignatureKey(key, dateStamp, regionName, serviceName):
        """Generate v4 signature.

        Generate v4 signature based on key, datestamp, region and
        service name.
        """
        kDate = AWSV4Signer._sign(('AWS4' + key).encode('utf-8'), dateStamp)
        kRegion = AWSV4Signer._sign(kDate, regionName)
        kService = AWSV4Signer._sign(kRegion, serviceName)
        kSigning = AWSV4Signer._sign(kService, 'aws4_request')
        return kSigning

    def _create_string_to_sign_v4(
            self,
            method='',
            canonical_uri='',
            canonical_query_string='',
            body='',
            epoch_t='',
            algorithm='',
            host='',
            service='',
            region=''):
        """Generates string_to_sign for authorization key generation."""
        canonical_request = self._create_canonical_request(
            method, canonical_uri, canonical_query_string, body, epoch_t, host)
        credential_scope = AWSV4Signer._get_date(epoch_t) + '/' + \
            region + '/' + service + '/' + 'aws4_request'

        string_to_sign = algorithm + '\n' + \
            AWSV4Signer._get_amz_timestamp(epoch_t) + '\n' + \
            credential_scope + '\n' + \
            hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

        return string_to_sign

    # Helper method.
    def _get_date(epoch_t):
        """Return date in Ymd format."""
        return epoch_t.strftime('%Y%m%d')

    # Helper method.
    def _get_amz_timestamp(epoch_t):
        """Return timestamp in YMDTHMSZ format."""
        return epoch_t.strftime('%Y%m%dT%H%M%SZ')

    # Helper Helper method for generating request_uri for v4 signing.
    def fmt_s3_request_uri(bucket_name, object_name=None):
        # The URL quoting functions focus on taking program data and making
        # it safe for use as URL components by quoting special characters
        # and appropriately encoding non-ASCII text.
        # urllib.parse.urlencode converts a mapping object or a sequence of
        # two-element tuples, which may contain str or bytes objects,
        # to a percent-encoded ASCII text string.
        # https://docs.python.org/3/library/urllib.parse.html

        request_uri = '/' + urllib.parse.quote(bucket_name, safe='')
        if object_name is not None:
            request_uri = request_uri + '/' + \
                urllib.parse.quote(object_name, safe='')
        return request_uri

    # generating AWS v4 Authorization signature
    def sign_request_v4(
            self,
            method=None,
            canonical_uri='/',
            canonical_query_string='',
            body='',
            epoch_t='',
            host='',
            service='',
            region=''):
        """Generate authorization signature."""
        if method is None:
            print("method can not be null")
            return None
        credential_scope = AWSV4Signer._get_date(epoch_t) + '/' + region + \
            '/' + service + '/' + 'aws4_request'

        headers = AWSV4Signer._get_headers(host, epoch_t, body)
        sorted_headers = sorted([k for k in headers])
        signed_headers = "{}".format(";".join(sorted_headers))

        algorithm = 'AWS4-HMAC-SHA256'

        string_to_sign = self._create_string_to_sign_v4(
            method,
            canonical_uri,
            canonical_query_string,
            body,
            epoch_t,
            algorithm,
            host,
            service,
            region)

        signing_key = AWSV4Signer._getV4SignatureKey(
            self._secret_key, AWSV4Signer._get_date(epoch_t), region, service)

        signature = hmac.new(
            signing_key,
            (string_to_sign).encode('utf-8'),
            hashlib.sha256).hexdigest()

        authorization_header = algorithm + ' ' + 'Credential=' + \
            self._access_key + '/' + credential_scope + ', ' + \
            'SignedHeaders=' + signed_headers + \
            ', ' + 'Signature=' + signature
        return authorization_header

    # generating AWS v4 signature header
    def prepare_signed_header(
            self,
            http_request,
            request_uri,
            query_params,
            body,
            read_range=None):
        """
        Generate headers used for authorization requests.

        Parameters:

        http_request - Any of http verbs: GET, PUT, DELETE, POST
        request_uri - URL safe resource string,
                      example /bucket_name/object_name
        query_params - URL safe query param string,
                      example param1=abc&param2=somevalue
        body - content
        Range - range of bytes string,
                example : total_read_bytes = range_start - range_end

        Returns:
            headers dictionary with following header keys: Authorization,
            x-amz-date, and x-amz-content-sha256

        Sample usage: headers =
            AWSV4Signer("http://s3.seagate.com", "cortxs3", 'us-west2',
                        access_key, secret_key).prepare_signed_header(
                                'PUT', request_uri, query_params, body)
        """
        url_parse_result = urllib.parse.urlparse(self._endpoint)
        epoch_t = datetime.datetime.utcnow()
        headers = {'content-type': 'application/x-www-form-urlencoded',
                   'Accept': 'text/plain'}

        # Add range header field in request headers
        if read_range is not None:
            headers['Range'] = read_range

        # Generate the signature and setup Authorization header.
        headers['Authorization'] = self.sign_request_v4(
            http_request,
            request_uri,
            query_params,
            body,
            epoch_t,
            url_parse_result.netloc,
            self._service_name,
            self._region)

        # Setup std headers
        headers['x-amz-date'] = AWSV4Signer._get_amz_timestamp(epoch_t)
        # generated in _create_canonical_request()
        headers['x-amz-content-sha256'] = self._body_hash_hex
        return headers
