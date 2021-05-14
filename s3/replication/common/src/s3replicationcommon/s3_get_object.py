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
from s3replicationcommon.aws_v4_signer import AWSV4Signer


class S3AsyncGetObject:
    def __init__(self, session, bucket_name, object_name):
        """Initialise."""
        self._session = session
        self._bucket_name = bucket_name
        self._object_name = object_name

    # yields data chunk for given size
    async def fetch(self, chunk_size):
        request_uri = AWSV4Signer.fmt_s3_request_uri(
            self._bucket_name, self._object_name)

        query_params = ""
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
            print("Failed to generate v4 signature")
            sys.exit(-1)

        print('GET on {}'.format(self._session.endpoint + request_uri))
        async with self._session.get_client_session().get(
                self._session.endpoint + request_uri, headers=headers) as resp:
            while True:
                data_chunk = await resp.content.read(chunk_size)
                if not data_chunk:
                    break
                print(data_chunk)
                yield data_chunk
            print('GET Object http status: {}'.format(resp.status))
