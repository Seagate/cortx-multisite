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

import logging
from s3replicationcommon.s3_session import S3Session

_logger = logging.getLogger('s3replicator')

# Session cache is managed as a dict with keys as combination of endpoint and
# access key to uniquely identify each session for an IAM account/user.


def get_session(app, s3_site, access_key, secret_key, max_connections):

    # example "s3.seagate.com|someaccesskey"
    session_key = s3_site.get_netloc() + "|" + access_key

    session = app["sessions"].get(session_key, None)
    if session is None:
        _logger.debug("Creating new session for session_key {}".
                      format(session_key))
        # Create New session
        session = S3Session(
            _logger,
            s3_site,
            access_key,
            secret_key,
            max_connections)

        # Cache it
        app["sessions"][session_key] = session
    else:
        _logger.debug("Reusing session for session_key {}".
                      format(session_key))

    return app["sessions"][session_key]


async def close_all_sessions(app):
    for session_key, session in app["sessions"].items():
        _logger.debug("Closing session for session_key {}".format(session_key))
        await session.close()
