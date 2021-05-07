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
import sys

"""Custom log level which is more verbose than DEBUG"""
TRACE: int = 5

__all__ = ['TRACE', 'setup_logging']

def setup_logging(logger_name: str, log_level: int = logging.DEBUG):
    """
    Initializes the logging for the whole application.
    Registers special 'multisite' named logger, configures the logging format and
    sets the verbosity level to `log_level`.
    Register custom verbosity level called TRACE. Here is the example
    how tracing can be done:
            LOG.log(TRACE, 'This is a trace message')
    Note: This function must be invoked before any logging happens.
    """
    # INFO = 20, DEBUG = 10, so trace is less than DEBUG
    logging.addLevelName(TRACE, 'TRACE')

    # Get logger name from user and register
    LOG = logging.getLogger(logger_name)
    LOG.setLevel(log_level)

    # Create formatter for console handler
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] %(message)s')
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    # Register handler to logger
    LOG.addHandler(console)

    return LOG
