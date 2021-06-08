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

# prepare_job.py
#
# This file contains class which helps to create
# replication job preparation from s3 metadata


import os
import yaml
import datetime
import json
import uuid


class PrepareReplicationJob:

    def __init__(self):
        """Replication manager's job id."""

        # Job id for replication manager's reference
        self.rm_job_id = str(uuid.uuid4())

    @classmethod
    def from_fdmi(cls, fdmi_record):
        """Prepare replication job record from fdmi record."""

        # Read the config file.
        with open(os.path.join(
                os.path.dirname(__file__), '..',
                'config/source_target_s3_config.yaml'), 'r') as config:
            config = yaml.safe_load(config)

        # File with credentials. ~/.cortxs3/credentials.yaml
        creds_home = os.path.join(os.path.expanduser('~'), '.cortxs3')
        creds_file_path = os.path.join(creds_home, 'credentials.yaml')

        credentials_config = None
        with open(creds_file_path, 'r') as cred_config:
            credentials_config = yaml.safe_load(cred_config)

        template_file = os.path.join(os.path.dirname(__file__), '..',
                                     'config/replication_job_template.json')
        with open(template_file, 'r') as file_content:
            job_dict = json.load(file_content)

        # Update the fields in template.
        epoch_t = datetime.datetime.utcnow()

        job_dict["replication-id"] = config["source_bucket_name"] + \
            fdmi_record["Object-Name"] + str(epoch_t)
        job_dict["replication-event-create-time"] = epoch_t.strftime(
            '%Y%m%dT%H%M%SZ')

        job_dict["source"]["endpoint"] = config["endpoint"]
        job_dict["source"]["service_name"] = config["s3_service_name"]
        job_dict["source"]["region"] = config["s3_region"]

        job_dict["source"]["access_key"] = credentials_config["access_key"]
        job_dict["source"]["secret_key"] = credentials_config["secret_key"]

        job_dict["source"]["operation"]["attributes"]["Bucket-Name"] = \
            config["source_bucket_name"]
        job_dict["source"]["operation"]["attributes"]["Object-Name"] = \
            fdmi_record["Object-Name"]
        job_dict["source"]["operation"]["attributes"]["Content-Length"] = \
            fdmi_record["System-Defined"]["Content-Length"]
        job_dict["source"]["operation"]["attributes"]["Content-MD5"] = \
            fdmi_record["System-Defined"]["Content-MD5"]
        job_dict["source"]["operation"]["attributes"]["Content-Type"] = \
            fdmi_record["System-Defined"]["Content-Type"]
        job_dict["source"]["operation"]["attributes"]["Date"] = \
            fdmi_record["System-Defined"]["Date"]
        job_dict["source"]["operation"]["attributes"]["Last-Modified"] = \
            fdmi_record["System-Defined"]["Last-Modified"]
        job_dict["source"]["operation"]["attributes"]["Owner-Account"] = \
            fdmi_record["System-Defined"]["Owner-Account"]
        job_dict["source"]["operation"]["attributes"]["Owner-Account-id"] = \
            fdmi_record["System-Defined"]["Owner-Account-id"]
        job_dict["source"]["operation"]["attributes"]["Owner-Canonical-id"] = \
            fdmi_record["System-Defined"]["Owner-Canonical-id"]
        job_dict["source"]["operation"]["attributes"]["Owner-User"] = \
            fdmi_record["System-Defined"]["Owner-User"]
        job_dict["source"]["operation"]["attributes"]["Owner-User-id"] = \
            fdmi_record["System-Defined"]["Owner-User-id"]
        job_dict["source"]["operation"]["attributes"]["x-amz-version-id"] = \
            fdmi_record["System-Defined"]["x-amz-version-id"]

        job_dict["target"]["endpoint"] = config["endpoint"]
        job_dict["target"]["service_name"] = config["s3_service_name"]
        job_dict["target"]["region"] = config["s3_region"]
        job_dict["target"]["access_key"] = credentials_config["access_key"]
        job_dict["target"]["secret_key"] = credentials_config["secret_key"]

        job_dict["target"]["Bucket-Name"] = config["target_bucket_name"]

        return job_dict
