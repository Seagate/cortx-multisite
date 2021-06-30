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

import os
import yaml


class Config:

    """Configuration for S3 tests."""

    def __init__(self):
        """Initialise."""
        # Read the config file.
        with open(os.path.join(os.path.dirname(__file__),
                  'config/config.yaml'), 'r') as config:
            self._config = yaml.safe_load(config)

        # File with credentials. ~/.cortxs3/credentials.yaml
        creds_home = os.path.join(os.path.expanduser('~'), '.cortxs3')
        creds_file_path = os.path.join(creds_home, 'credentials.yaml')

        credentials_config = None
        with open(creds_file_path, 'r') as config:
            credentials_config = yaml.safe_load(config)

        self.endpoint = self._config["endpoint"]
        self.s3_service_name = self._config["s3_service_name"]
        self.s3_region = self._config["s3_region"]

        self.access_key = credentials_config["access_key"]
        self.secret_key = credentials_config["secret_key"]

        self.source_bucket_name = self._config["source_bucket_name"]
        self.target_bucket_name = self._config["target_bucket_name"]
        self.object_name_prefix = self._config["object_name_prefix"]
        self.object_size = self._config["object_size"]
        self.transfer_chunk_size = self._config["transfer_chunk_size"]
        self.max_s3_connections = self._config["max_s3_connections"]
