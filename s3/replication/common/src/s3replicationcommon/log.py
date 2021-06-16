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
import logging.handlers
import os
import sys
import yaml


def fmt_reqid_log(request_id=None):
    """Generates formatted string with request id for logging.

    Args
    -----
        request_id (str, optional): ID used in logs for easy debugging.
        Defaults to None.
    """
    message = ""
    if request_id is not None:
        message = "RequestId [{}]: ".format(request_id)
    return message


def setup_logger(logger_name: str, log_config_file: str):
    """
    Sets up a logger with given name and log properties defined in
    log_config_file yaml.

    Returns:
        None on failure
        logger on success
    """

    logger = logging.getLogger(logger_name)

    log_props = None
    with open(log_config_file, 'r') as file_config:
        # Load yaml
        log_props = yaml.safe_load(file_config)

        if logger_name != log_props["logger_name"]:
            print("logger_name {} does not match {} in log config file."
                  .format(logger_name, log_props["logger_name"]))
            return None

        # Setup the File logger
        # Setup default logger to debug so specific handlers can filter
        # as per handler specific log level
        logger.setLevel(logging.DEBUG)

        file_formatter = logging.Formatter(log_props["file"]["log_format"])

        log_dir = log_props["file"]["path"]
        # Create log directory if not present
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create handler for logfile rotation
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, log_props["file"]["log_filename"]),
            maxBytes=log_props["file"]["max_size_in_bytes"],
            backupCount=log_props["file"]["backup_count"])

        # setup the file logging level
        file_handler.setLevel(
            logging.getLevelName(
                log_props["file"]["log_level"]))

        # Set formatter for file log handler
        file_handler.setFormatter(file_formatter)

        # Register handler with file logger
        logger.addHandler(file_handler)

        # Setup the Console logger if enabled
        if log_props["console"]["enabled"]:
            print(("Setting up console handler..."))
            console_formatter = logging.Formatter(
                log_props["console"]["log_format"])

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)

            # setup the console logging level
            console_handler.setLevel(
                logging.getLevelName(
                    log_props["console"]["log_level"]))

            # Register handler to logger
            logger.addHandler(console_handler)
    return logger
