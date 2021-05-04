#!/usr/bin/env python3

# Replication manager config
#
# This file contains config class and
# functions to apply config

import sys
import os
import shutil
import logging
import yaml
import uuid
import glob
import logging.handlers

class Config:
    """ configuratio for manager """

    rep_conf = {}
    logfile_name = 'default.log'
    logfile_size = 5242880 # default 5MB
    rotation = 5
    location = './'
    host = '127.0.0.0'
    port = 8080
    configfile = './config.yaml'

    def __init__(self, userconfig='manager_conf.yaml'):
        """config class constructor"""
        self.logger = logging.getLogger('manager_proc')
        self.logger.setLevel(logging.DEBUG)

        if userconfig != None:
            self.configfile = userconfig

        self.load_config()
        self.set_config()

        # Add the log message handler to the logger
        formatter=logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] %(message)s')
        if not os.path.exists(self.location):
            os.makedirs(self.location)
        logfile = str(self.location)+str(self.logfile_name)
        handler = logging.handlers.RotatingFileHandler(
            logfile ,maxBytes=self.logfile_size, backupCount=self.rotation)
        handler.setFormatter(formatter)
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
