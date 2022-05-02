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

# Replication manager configuration

import os
import yaml


class Config:
    def __init__(self, configfile):
        """Initialise."""
        if configfile is None:
            # Default config file directory : ~/.cortxs3/manager
            config_home = os.path.join(
                os.path.expanduser('~'), '.cortxs3', 'manager')
            configfile = os.path.join(config_home, 'config.yaml')
            if os.path.isfile(configfile):
                self.configfile = configfile
            else:
                self.configfile = os.path.join(os.path.dirname(__file__),
                                               '..', 'config', 'config.yaml')
        else:
            self.configfile = os.path.expanduser(configfile)

        print(
            "Config file location : {}".format(
                self.configfile))

        self.host = '127.0.0.1'
        self.port = 8080

    def load(self):
        """Load the configuration data.

        This method loads the configuration data from a config file
        and sets up members to be used within application.

        Returns:
        --------
            on success returns self
        """
        with open(self.configfile, 'r') as file_config:
            config_props = yaml.safe_load(file_config)

            self.host = config_props['manager']['host']
            self.port = config_props['manager']['port']
            self.ssl = config_props['manager']['ssl']
            self.service_name = config_props['manager']['service_name']
            self.job_polling_interval = \
                config_props['manager']['job_polling_interval']
        return self

    def print_with(self, logger):
        if logger is not None:
            logger.info("Using configuration:")
            logger.info("Host: {}".format(self.host))
            logger.info("Port: {}".format(self.port))
            logger.info("ssl: {}".format(self.ssl))
            logger.info("service_name: {}".format(self.service_name))
            logger.info(
                "job_polling_interval: {}".format(
                    self.job_polling_interval))
