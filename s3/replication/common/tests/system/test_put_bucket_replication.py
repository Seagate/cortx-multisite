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

import os
import subprocess
import fileinput
from config import Config


def main():

    config = Config()

    # CONFIG OPTIONS
    bucket_name = config.source_bucket_name
    dest_bucket_name = config.target_bucket_name
    object_name_prefix = config.object_name_prefix
    iam_role = config.iam_role

    # Create temp replication policy file.
    subprocess.call(['cp',
                     './tests/system/config/replication_policy_sample.json',
                     'temp_policy.json'])

    matches = ['ROLE_ID', 'REPLICATION_ENABLED_BUCKET']

    # Read policy and make replacements based on config options.
    with fileinput.FileInput('temp_policy.json', inplace=True) as file:

        # Read each line and match the pattern and do replacement.
        for line in file:
            if all(x in line for x in matches):
                line2 = line.replace('ROLE_ID', str(iam_role))
                print(
                    line2.replace(
                        'REPLICATION_ENABLED_BUCKET',
                        bucket_name),
                    end='')
            elif 'DESTINATION_BUCKET' in line:
                print(
                    line.replace(
                        'DESTINATION_BUCKET',
                        dest_bucket_name),
                    end='')

            elif 'PREFIX' in line:
                print(
                    line.replace(
                        'PREFIX',
                        object_name_prefix),
                    end='')
            else:
                print(line, end='')

    # Print modified policy on console.
    subprocess.call(['cat', 'temp_policy.json'])

    command = 'aws s3api put-bucket-replication --bucket ' + \
        bucket_name + ' --replication-configuration file://temp_policy.json'

    exit_status = os.system(command)

    if exit_status == 0:
        print("put-bucket-replication done! ")
    else:
        print("put-bucket-replication failed! ")
        os._exit(exit_status)

    # Delete temp file.
    os.system('rm -rf temp_policy.json')


main()
