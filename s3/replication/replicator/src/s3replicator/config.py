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


class Config:
    """ configuration for replicator """

    def __init__(self, configfile):
        """config class constructor"""

        if configfile is None:
            self.configfile = os.path.join(os.path.dirname(__file__),
                                           '..', 'config', 'config.yaml')
        else:
            self.configfile = configfile

        self.host = '127.0.0.1'
        self.port = 8081

    def load(self):
        """
        Load the configuration data.

        Returns:
            on success returns self
        """
        with open(self.configfile, 'r') as file_config:
            config_props = yaml.safe_load(file_config)

            self.host = config_props['replicator']['host']
            self.port = config_props['replicator']['port']
            self.ssl = config_props['replicator']['ssl']
            self.service_name = config_props['replicator']['service_name']
            self.transfer_chunk_size_bytes = \
                config_props['transfer']["transfer_chunk_size_bytes"]
        return self

    def print_with(self, logger):
        if logger is not None:
            logger.info("Using configuration:")
            logger.info("Host: {}".format(self.host))
            logger.info("Port: {}".format(self.port))
            logger.info("ssl: {}".format(self.ssl))
            logger.info("service_name: {}".format(self.service_name))
