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

# Replicator config
#
# This file contains config class and
# functions to apply config

import os
import yaml
from s3replicationcommon.s3_common import make_baseurl


class Config:

    """Configuration for replicator."""

    def __init__(self, configfile):
        """Initialise."""
        if configfile is None:
            self.configfile = os.path.join(os.path.dirname(__file__),
                                           '..', 'config', 'config.yaml')
        else:
            self.configfile = configfile

        self.host = '127.0.0.1'
        self.port = 8081
        self.max_connections_per_s3_session = 100

    def load(self):
        """Load the configuration data."""
        with open(self.configfile, 'r') as file_config:
            config_props = yaml.safe_load(file_config)

            self.host = config_props['replicator']['host']
            self.port = config_props['replicator']['port']
            self.ssl = config_props['replicator']['ssl']
            self.service_name = config_props['replicator']['service_name']

            self.max_replications = \
                config_props['transfer']["max_replications"]
            self.transfer_chunk_size_bytes = \
                config_props['transfer']["transfer_chunk_size_bytes"]
            self.max_connections_per_s3_session = \
                config_props['transfer']['max_connections_per_s3_session']

            self.job_cache_enabled = config_props['jobs']['enable_cache']
            self.job_cache_timeout_secs = config_props['jobs']['cache_timeout']

            self.manager_host = config_props['manager']['host']
            self.manager_port = config_props['manager']['port']
            self.manager_ssl = config_props['manager']['ssl']
            self.manager_service_name = config_props['manager']['service_name']
        return self

    def get_replicator_endpoint(self):
        """Returns replicator endpoint."""
        scheme = "http"
        if self.ssl:
            scheme = "https"
        # example http://localhost:8080
        return make_baseurl(scheme, self.host, self.port)

    def get_replication_manager_endpoint(self):
        """Returns replication manager endpoint."""
        scheme = "http"
        if self.manager_ssl:
            scheme = "https"
        # example http://localhost:8080
        return make_baseurl(scheme, self.manager_host, self.manager_port)

    def print_with(self, logger):
        if logger is not None:
            logger.info("Using configuration:")
            logger.info("Host: {}".format(self.host))
            logger.info("Port: {}".format(self.port))
            logger.info("ssl: {}".format(self.ssl))
            logger.info("service_name: {}".format(self.service_name))

            logger.info("transfer_chunk_size_bytes: {}".format(
                self.transfer_chunk_size_bytes))
            logger.info("max_replications: {}".format(self.max_replications))
            logger.info("max_connections_per_s3_session: {}".format(
                self.max_connections_per_s3_session))

            logger.info("manager_host: {}".format(self.manager_host))
            logger.info("manager_port: {}".format(self.manager_port))
            logger.info("manager_ssl: {}".format(self.manager_ssl))
            logger.info("manager_service_name: {}".format(
                self.manager_service_name))
