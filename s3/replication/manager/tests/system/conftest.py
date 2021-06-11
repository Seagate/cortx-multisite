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

import asyncio
import os
import pytest
import sys
import yaml

from s3replicationcommon.log import setup_logger


@pytest.fixture
def event_loop():
    """Fixture for async operations."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def logger():
    """Setup logger for tests."""
    # Setup logging and get logger
    log_config_file = os.path.join(
        os.path.dirname(__file__), 'config', 'logger_config.yaml')
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        sys.exit(-1)
    return logger


@pytest.fixture
def test_config(logger):
    """Fixture for Replication manager host, port configuration."""
    host = '127.0.0.1'
    port = '8080'

    # Replication manager Connection config
    config_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'src', 'config', 'config.yaml')
    logger.debug("Using Replication manager config from {}".
                 format(config_path))

    with open(config_path, 'r') as file_config:
        config = yaml.safe_load(file_config)
        host = config['manager'].get('host')
        port = str(config['manager'].get('port'))

    # URL for non-secure http endpoint
    url = 'http://' + host + ':' + port

    return {'url': url}
