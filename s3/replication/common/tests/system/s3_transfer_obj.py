#!/usr/bin/env python3

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

import asyncio
from config import Config
from s3replicationcommon.s3_site import S3Site
from s3replicationcommon.s3_session import S3Session
from s3replicationcommon.s3_get_object import S3AsyncGetObject
from s3replicationcommon.s3_put_object import S3AsyncPutObject


async def main():

    config = Config()

    s3_site = S3Site(config.endpoint, config.s3_service_name, config.s3_region)

    session = S3Session(s3_site, config.access_key, config.secret_key)

    object_reader = S3AsyncGetObject(session, "kdtest", "creds")
    object_writer = S3AsyncPutObject(session, "kdtest", "creds-copy")

    # Start transfer
    await object_writer.send(object_reader, config.transfer_size)
    await session.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
