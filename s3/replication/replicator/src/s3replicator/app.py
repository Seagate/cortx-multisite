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

from aiohttp import web
from .config import Config
import logging
from s3replicationcommon.log import setup_logging
from .replicator_routes import routes
from .jobs import Jobs

# Setup log
LOG = logging.getLogger('replicator')

class ReplicatorApp:
    def __init__(self, configfile):
        """Initialise logger and configuration"""

        self._config = Config(configfile)
        setup_logging('replicator')
        self._jobs = Jobs()
        self._jobs_in_progress = Jobs()

        LOG.debug('HOST is : {}'.format(self._config.host))
        LOG.debug('PORT is : {}'.format(self._config.port))

    def run(self):
        """Start replicator"""
        app = web.Application()
        # Setup the global context store.
        # https://docs.aiohttp.org/en/stable/web_advanced.html#application-s-config
        app['all_jobs'] = self._jobs
        app['replication-managers'] = []  # TBD

        # Setup application routes.
        app.add_routes(routes)

        # Start the REST server.
        web.run_app(app, host=self._config.host, port=self._config.port)
