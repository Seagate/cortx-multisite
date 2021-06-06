import os
import yaml
import datetime
import json


class PrepareJob():

    def __init__(self):
        # XXX
        self.rm_job_id = ''

    def prepare_replication_job(self, object_info):

        # Read the config file.
        with open(os.path.join(os.path.dirname(__file__), '..', 'config/s3_config.yaml'), 'r') as config:
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
        print('template file :\n {}'.format(job_dict))
        print('config file :\n {}'.format(config))
        print('object_info :\n {} \n object_name : {}'.format(
            object_info, object_info["Object-Name"]))
        job_dict["replication-id"] = config["source_bucket_name"] + \
            object_info["Object-Name"] + str(epoch_t)
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
            object_info["Object-Name"]
        job_dict["source"]["operation"]["attributes"]["Content-Length"] = \
            object_info["System-Defined"]["Content-Length"]
        job_dict["source"]["operation"]["attributes"]["Content-MD5"] = \
            object_info["System-Defined"]["Content-MD5"]
        job_dict["source"]["operation"]["attributes"]["Content-Type"] = \
            object_info["System-Defined"]["Content-Type"]
        job_dict["source"]["operation"]["attributes"]["Date"] = \
            object_info["System-Defined"]["Date"]
        job_dict["source"]["operation"]["attributes"]["Last-Modified"] = \
            object_info["System-Defined"]["Last-Modified"]
        job_dict["source"]["operation"]["attributes"]["Owner-Account"] = \
            object_info["System-Defined"]["Owner-Account"]
        job_dict["source"]["operation"]["attributes"]["Owner-Account-id"] = \
            object_info["System-Defined"]["Owner-Account-id"]
        job_dict["source"]["operation"]["attributes"]["Owner-Canonical-id"] = \
            object_info["System-Defined"]["Owner-Canonical-id"]
        job_dict["source"]["operation"]["attributes"]["Owner-User"] = \
            object_info["System-Defined"]["Owner-User"]
        job_dict["source"]["operation"]["attributes"]["Owner-User-id"] = \
            object_info["System-Defined"]["Owner-User-id"]
        job_dict["source"]["operation"]["attributes"]["x-amz-version-id"] = \
            object_info["System-Defined"]["x-amz-version-id"]

        job_dict["target"]["endpoint"] = config["endpoint"]
        job_dict["target"]["service_name"] = config["s3_service_name"]
        job_dict["target"]["region"] = config["s3_region"]
        job_dict["target"]["access_key"] = credentials_config["access_key"]
        job_dict["target"]["secret_key"] = credentials_config["secret_key"]

        job_dict["target"]["Bucket-Name"] = config["target_bucket_name"]

        return job_dict
