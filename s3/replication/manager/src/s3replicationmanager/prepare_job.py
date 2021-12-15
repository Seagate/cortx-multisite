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

import datetime
import os
import yaml

from configparser import ConfigParser
from s3replicationcommon.templates import replication_job_template


class PrepareReplicationJob:

    @staticmethod
    def from_fdmi(fdmi_record):
        """Prepare replication job record from fdmi record."""

        # XXX All below, source/target credentials logic to change after
        # S3 server changes are ready for setting up replication.

        # Read the config file for source/target sites.
        cortx_s3 = None
        conf_path = os.path.join(os.path.expanduser('~'), '.cortxs3')
        file_path = os.path.join(conf_path, "cortx_s3.yaml")
        if not os.path.isfile(file_path):
            file_path = os.path.join(
                os.path.dirname(__file__), '..', 'config/cortx_s3.yaml')

        with open(file_path, 'r') as cortx_s3_f:
            cortx_s3 = yaml.safe_load(cortx_s3_f)

        aws_s3 = None
        file_path = os.path.join(conf_path, "aws_s3.yaml")
        if not os.path.isfile(file_path):
            file_path = os.path.join(
                os.path.dirname(__file__), '..', 'config/aws_s3.yaml')

        with open(file_path, 'r') as aws_s3_f:
            aws_s3 = yaml.safe_load(aws_s3_f)

        # File with credentials. ~/.cortxs3/credentials.yaml
        cortx_creds_path = os.path.join(conf_path, 'credentials.yaml')

        cortx_credentials = None
        with open(cortx_creds_path, 'r') as cred_config:
            cortx_credentials = yaml.safe_load(cred_config)

        # For AWS target.
        # File with credentials. ~/.aws/credentials
        aws_s3_creds_home = os.path.join(os.path.expanduser('~'), '.aws')
        aws_s3_creds_path = os.path.join(aws_s3_creds_home, 'credentials')

        aws_s3_credentials = ConfigParser()
        aws_s3_credentials.read(aws_s3_creds_path)

        job_dict = replication_job_template()

        # Update the fields in template.
        epoch_t = datetime.datetime.utcnow()

        # Combination of following fields makes S3 metadata update unique.
        job_dict["replication-id"] = fdmi_record["Bucket-Name"] + '_' + \
            fdmi_record["Object-Name"] + '_' + \
            fdmi_record["System-Defined"]["x-amz-version-id"] + '_' + \
            fdmi_record["create_timestamp"] + '_' + \
            epoch_t.strftime('%Y%m%dT%H%M%SZ')

        job_dict["replication-event-create-time"] = epoch_t.strftime(
            '%Y%m%dT%H%M%SZ')

        job_dict["source"]["endpoint"] = cortx_s3["endpoint"]

        if "admin_endpoint" in cortx_s3:
            job_dict["source"]["admin_endpoint"] = cortx_s3["admin_endpoint"]
        job_dict["source"]["service_name"] = cortx_s3["s3_service_name"]
        job_dict["source"]["region"] = cortx_s3["s3_region"]

        job_dict["source"]["access_key"] = cortx_credentials["access_key"]
        job_dict["source"]["secret_key"] = cortx_credentials["secret_key"]

        job_dict["source"]["operation"]["attributes"]["Bucket-Name"] = \
            fdmi_record["Bucket-Name"]
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

        # if tags are present # need to remove if record lacks this field.
        if "User-Defined-Tags" in fdmi_record.keys():
            job_dict["source"]["operation"]["type"] = "replicate_object_tags"
            job_dict["User-Defined-Tags"] = fdmi_record["User-Defined-Tags"]

        # XXX: Change after S3 changes are ready for replication.
        if fdmi_record["User-Defined"]["x-amz-meta-target-site"] == "cortxs3":
            job_dict["target"]["endpoint"] = cortx_s3["endpoint"]
            job_dict["target"]["service_name"] = cortx_s3["s3_service_name"]
            job_dict["target"]["region"] = cortx_s3["s3_region"]
            job_dict["target"]["access_key"] = cortx_credentials["access_key"]
            job_dict["target"]["secret_key"] = cortx_credentials["secret_key"]
        elif fdmi_record["User-Defined"]["x-amz-meta-target-site"] == "awss3":
            job_dict["target"]["endpoint"] = aws_s3["endpoint"]
            job_dict["target"]["service_name"] = aws_s3["s3_service_name"]
            job_dict["target"]["region"] = aws_s3["s3_region"]
            job_dict["target"]["access_key"] = \
                aws_s3_credentials["default"]["aws_access_key_id"]
            job_dict["target"]["secret_key"] = \
                aws_s3_credentials["default"]["aws_secret_access_key"]
        else:
            # Invalid record.
            return None

        job_dict["target"]["Bucket-Name"] = \
            fdmi_record["User-Defined"]["x-amz-meta-target-bucket"]

        return job_dict
