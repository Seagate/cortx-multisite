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
import sys
from aiohttp import web
import logging
from .config import Config
from s3replicationcommon.log import setup_logger
from s3replicationcommon.jobs import Jobs
from .replicator_routes import routes
from .replication_manager import ReplicationManager
from .replication_managers import ReplicationManagers
from .session_manager import close_all_sessions

_logger = logging.getLogger('s3replicator')


async def on_startup(app):
    _logger.debug("Starting server...")
    # Currently only one replication manager is registered.
    config = app["config"]
    managers_list = app['replication-managers']

    remote_endpoint = config.get_replication_manager_endpoint()
    replication_manager = ReplicationManager(remote_endpoint)
    connected = await replication_manager.subscribe(
        config.get_replicator_endpoint(), config.max_replications)
    if connected:
        _logger.debug("Subscribed successfully for jobs...")
        managers_list[replication_manager.id] = replication_manager
    else:
        await close_all_sessions(app)
        await replication_manager.close()
        _logger.error("Failed to subscribe for jobs...")
        sys.exit(-1)


async def on_shutdown(app):
    _logger.debug("Performing cleanup on shutdown...")
    await close_all_sessions(app)
    await app['replication-managers'].close()


class ReplicatorApp:
    def __init__(self, config_file, log_config_file):
        """Initialise logger and configuration."""
        self._config = Config(config_file)
        if self._config.load() is None:
            print("Failed to load configuration.\n")
            sys.exit(-1)

        # Setup logging.
        self._logger = setup_logger('s3replicator', log_config_file)
        if self._logger is None:
            print("Failed to configure logging.\n")
            sys.exit(-1)

        self._inprogress_jobs = Jobs(self._logger, "all-jobs")
        if self._config.job_cache_enabled:
            self._completed_jobs = Jobs(
                self._logger, "completed-jobs",
                self._config.job_cache_timeout_secs)
        else:
            self._completed_jobs = Jobs(self._logger, "completed-jobs")

        self._replication_managers = ReplicationManagers()

        self._config.print_with(self._logger)

    def run(self):
        """Start replicator."""
        app = web.Application(client_max_size=self._config.max_payload)
        # Setup the global context store.
        # https://docs.aiohttp.org/en/stable/web_advanced.html#application-s-config

        # Each site (source or target) for given account/user will have one
        # session instance which will be reused for each request for that site.
        # Example {"src.s3.seagate.com|access_key": aiohttp.ClientSession(),
        # "tgt.s3.seagate.com|access_key": aiohttp.ClientSession()}
        # See session_manager.py
        app["sessions"] = {}
        app["config"] = self._config

        # All scheduled jobs
        app['all_jobs'] = self._inprogress_jobs
        # completed = successfully completed, failed, or aborted and cached
        app['completed_jobs'] = self._completed_jobs
        app['replication-managers'] = self._replication_managers

        # Throttle:  Allow only Max replications to run at a moment.
        # Alternative design option is to use queued requests.
        app['semaphore'] = asyncio.Semaphore(self._config.max_replications)

        # Setup application routes.
        app.add_routes(routes)

        # Setup startup/shutdown handlers
        app.on_startup.append(on_startup)
        app.on_shutdown.append(on_shutdown)

        # Start the REST server.
        web.run_app(app, host=self._config.host, port=self._config.port)
