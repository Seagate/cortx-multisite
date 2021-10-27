# This is an experiment object tag replication request
# Please note : The original data fields could be different.
# Make sure to install all modules

import argparse
import requests
import json
from requests.structures import CaseInsensitiveDict

url = "http://127.0.0.1:8080/jobs"

# Request header fields
headers = CaseInsensitiveDict()
headers["Content-Type"] = "application/json"
headers["Accept"] = "text/plain"

# Create a parser and parse the arguments
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-s', type=str, required=True, help="source bucket")
arg_parser.add_argument('-o', type=str, required=True, help="source object")
arg_parser.add_argument('-l', type=str, required=True, help="object length")
arg_parser.add_argument('-t', type=str, required=True, help="target bucket")

args = arg_parser.parse_args()

source_bucket = args.s
object_name = args.o
object_length = args.l
target_bucket = args.t

data = {'ACL': '',
        'Bucket-Name': source_bucket,
        'Object-Name': object_name,
        'Object-URI': '',
        'System-Defined': {'Content-Length': object_length,
                           'Content-MD5': 'ccf003ff936fae257c9457a153779953',
                           'Content-Type': 'text/plain',
                           'Date': '2021-10-23T06:56:54.000Z',
                           'Last-Modified': '2021-10-23T06:56:54.000Z',
                           'Owner-Account': '',
                           'Owner-Account-id': '',
                           'Owner-Canonical-id': '',
                           'Owner-User': 'root',
                           'Owner-User-id': '',
                           'x-amz-server-side-encryption': 'None',
                           'x-amz-server-side-encryption-aws-kms-key-id': '',
                           'x-amz-server-side-encryption-customer-algorithm': '',
                           'x-amz-server-side-encryption-customer-key': '',
                           'x-amz-server-side-encryption-customer-key-MD5': '',
                           'x-amz-storage-class': 'STANDARD',
                           'x-amz-version-id': '',
                           'x-amz-website-redirect-location': 'None'},
        'User-Defined': {'x-amz-meta-replication': 'true',
                         'x-amz-meta-target-bucket': target_bucket,
                         'x-amz-meta-target-site': 'cortxs3'},
        'User-Defined-Tags': {},
        'create_timestamp': '2021-10-23T06:57:23.000Z',
        'layout_id': 3,
        'motr_oid': 'VA46AQAAAAA=-CQDwAQAA/Eg='}

resp = requests.post(url, headers=headers, data=json.dumps(data))
resp_status = resp.status_code

if resp_status == 201:
    print("HTTP status {} OK!".format(resp_status))
else:
    print("ERROR : BAD RESPONSE! status = {}".format(resp_status))
