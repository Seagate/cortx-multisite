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
from aiohttp import web
from .config import Config
from s3replicationcommon.log import setup_logger
from .replicator_routes import routes
from s3replicationcommon.jobs import Jobs


class ReplicatorApp:
    def __init__(self, config_file, log_config_file):
        """Initialise logger and configuration"""

        self._config = Config(config_file)
        if self._config.load() is None:
            print("Failed to load configuration.\n")
            sys.exit(-1)

        # Setup logging.
        self._logger = setup_logger('s3replicator', log_config_file)
        if self._logger is None:
            print("Failed to configure logging.\n")
            sys.exit(-1)

        self._jobs = Jobs()
        self._jobs_in_progress = Jobs()

        self._config.print_with(self._logger)

    def run(self):
        """Start replicator"""
        app = web.Application()
        # Setup the global context store.
        # https://docs.aiohttp.org/en/stable/web_advanced.html#application-s-config

        # Each site (source or target) will have one session instance which
        # will be reused for each request for that site.
        # Example {"site-1": aiohttp.ClientSession(), "site-2":
        # aiohttp.ClientSession()}
        app["sessions"] = {}
        app["config"] = self._config

        app['all_jobs'] = self._jobs
        app['replication-managers'] = []  # TBD

        # Setup application routes.
        app.add_routes(routes)

        # Start the REST server.
        web.run_app(app, host=self._config.host, port=self._config.port)
