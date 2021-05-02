#!/usr/bin/env python3

# Replicator config
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

class config():
    """ configuratio for replicator """

    rep_conf = None
    logfile_name = 'default.log'
    logfile_size = None
    rotation = None
    location = None
    host = None
    port = None

    def __init__(self):
        """config class constructor"""
        self.logger = logging.getLogger('replicator_proc')
        self.logger.setLevel(logging.DEBUG)
        self.load_config()
        self.set_config()

        # Add the log message handler to the logger
        formatter=logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] %(message)s')
        logfile = str(self.location)+str(self.logfile_name)
        handler = logging.handlers.RotatingFileHandler(
            logfile ,maxBytes=self.logfile_size, backupCount=self.rotation)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    @staticmethod
    def load_config(self):
        """Get configuration data."""
        self._conf_file = os.path.join(
            os.path.dirname(__file__), 'replicator_conf.yaml')#TODO : palcement
        with open(self._conf_file, 'r') as file_config:
            self.rep_conf = yaml.safe_load(file_config)

    def set_config(self):
        """set configurations."""
        self.host = self.rep_conf['replicator'].get('host')
        self.port = self.rep_conf['replicator'].get('port')
        self.logfile_name = self.rep_conf['logconfig'].get('log_file')
        self.logfile_size = self.rep_conf['logconfig'].get('max_bytes')
        self.rotation = self.rep_conf['logconfig'].get('backup_count')
        self.location = self.rep_conf['logconfig'].get('logger_directory')
