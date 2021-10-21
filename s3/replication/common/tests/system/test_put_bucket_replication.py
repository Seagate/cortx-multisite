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

#
# s3 get-bucket-replication api test script
# Usage : python3 test_s3_get_bucket_replication.py
#

import re
import os
import sys
import fileinput
from config import Config
from s3replicationcommon.log import setup_logger


def main():

    config = Config()

    # Setup logging and get logger
    log_config_file = os.path.join(os.path.dirname(__file__),
                                   'config', 'logger_config.yaml')

    print("Using log config {}".format(log_config_file))
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        print("Failed to configure logging.\n")
        sys.exit(-1)

    # CONFIG OPTIONS
    bucket_name = config.source_bucket_name
    dest_bucket_name = config.target_bucket_name
    object_name_prefix = str(config.object_name_prefix)
    iam_role = config.iam_role

    # Create temp replication policy file.
    os.system(
        'cp ./tests/system/config/replication_policy_sample.json temp_policy.json')

    matches = ['_ACCOUNT_ID_', '_REPLICATION_ENABLED_BUCKET_']

    # Read policy and make replacements based on config options.
    with fileinput.FileInput('temp_policy.json', inplace=True) as file:

        # Read each line and match the pattern and do replacement.
        for line in file:
            if all(x in line for x in matches):
                line = re.sub('(_ACCOUNT_ID_)', str(iam_role), line)
                line = re.sub(
                    '(_REPLICATION_ENABLED_BUCKET_)',
                    bucket_name,
                    line)
                print(line)
            elif '_DESTINATION_BUCKET_' in line:
                line = re.sub('(_DESTINATION_BUCKET_)', dest_bucket_name, line)
                print(line)
            elif '_PREFIX_' in line:
                line = re.sub('(_PREFIX_)', object_name_prefix, line)
                print(line)
            else:
                print(line, end='')

    # updated replication policy.
    # os.system('cat temp_policy.json')

    command = 'aws s3api put-bucket-replication --bucket ' + \
        bucket_name + ' --replication-configuration file://temp_policy.json'

    exit_status = os.system(command)

    if exit_status == 0:
        logger.info("put-bucket-replication passed! ")
    else:
        os.system('rm -rf temp_policy.json')
        logger.error("put-bucket-replication failed! ")
        os._exit(exit_status)

    # Delete temp file.
    os.system('rm -rf temp_policy.json')


main()
