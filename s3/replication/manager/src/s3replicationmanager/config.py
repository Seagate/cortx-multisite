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

# Replication manager config
#
# This file contains config class and
# functions to apply config

import os
import logging
import yaml
import logging.handlers

class Config:
    """ configuration for manager """

    def __init__(self, configfile):
        """config class constructor"""

        self.rep_conf = {}
        self.logfile_name = 'default.log'
        self.logfile_size = 5242880  # default 5MB
        self.rotation = 5
        self.location = './'
        self.host = '127.0.0.1'
        self.port = 8080
        self.configfile = os.path.join(os.path.dirname(__file__), '../config/config.yaml')

        # Get 'manager_proc' logger object
        self.logger = logging.getLogger('manager_proc')

        if configfile is not None:
            self.configfile = configfile

        # Load configuration
        self.load_config()

        # Set configuration to instance variable
        self.set_config()

        # Add the log message handler to the logger
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] %(message)s')
        if not os.path.exists(self.location):
            os.makedirs(self.location)
        logfile = str(self.location)+str(self.logfile_name)

        # Create handler for logfile rotation
        handler = logging.handlers.RotatingFileHandler(
            logfile, maxBytes=self.logfile_size, backupCount=self.rotation)

        # Set formatter for handler
        handler.setFormatter(formatter)

        # Register handler with logger
        self.logger.addHandler(handler)

    def load_config(self):
        """Get configuration data."""
        with open(self.configfile, 'r') as file_config:
            self.rep_conf = yaml.safe_load(file_config)

    def set_config(self):
        """set configurations."""
        self.host = self.rep_conf['manager'].get('host')
        self.port = self.rep_conf['manager'].get('port')
        self.logfile_name = self.rep_conf['logconfig'].get('log_file')
        self.logfile_size = self.rep_conf['logconfig'].get('max_bytes')
        self.rotation = self.rep_conf['logconfig'].get('backup_count')
        self.location = self.rep_conf['logconfig'].get('logger_directory')