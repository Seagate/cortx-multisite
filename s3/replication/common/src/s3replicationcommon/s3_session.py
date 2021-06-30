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


class S3Session:
    def __init__(self, logger, s3_site, access_key, secret_key,
                 number_of_connections=100):
        """Initialise S3 session."""
        self.logger = logger
        self.endpoint = s3_site.endpoint
        self.service_name = s3_site.service_name
        self.region = s3_site.region

        self.access_key = access_key
        self.secret_key = secret_key

        connector = aiohttp.TCPConnector(limit=number_of_connections)
        self._client_session = aiohttp.ClientSession(connector=connector)

    def get_client_session(self):
        return self._client_session

    async def close(self):
        await self._client_session.close()
