import sys
import boto3
from botocore.exceptions import ClientError


def get_s3(region=None):
    """
    Get a Boto 3 Amazon S3 resource with a specific AWS Region or with your
    default AWS Region.
    """
    return boto3.resource('s3', region_name=region) if region else boto3.resource('s3')


def list_my_buckets(s3):
    print('Buckets:\n\t', *[b.name for b in s3.buckets.all()], sep="\n\t")


def create_and_delete_my_bucket(bucket_name, region, keep_bucket):
    s3 = get_s3(region)

    list_my_buckets(s3)

    try:
        print('\nCreating new bucket:', bucket_name)
        bucket = s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': region
            }
        )
    except ClientError as e:
        print(e)
        sys.exit('Exiting the script because bucket creation failed.')

    bucket.wait_until_exists()
    list_my_buckets(s3)

    if not keep_bucket:
        print('\nDeleting bucket:', bucket.name)
        bucket.delete()

        bucket.wait_until_not_exists()
        list_my_buckets(s3)
    else:
        print('\nKeeping bucket:', bucket.name)

def create_1GB_file():
    f = open('newfile',"wb")
    f.seek(1073741824-1)
    f.write(b"\0")
    f.close()
    import os
    print(os.stat("newfile").st_size)

def list_my_buckets(s3):
    print('Buckets:\n\t', *[b.name for b in s3.buckets.all()], sep="\n\t")


def create_bucket(bucket_name, region):
    s3=get_s3(region)
    
    bucket = s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={
            'LocationConstraint': region
        }
    )


def enable_version(bucket_name, s3_resource):
    versioning = s3_resource.BucketVersioning(bucket_name)
    versioning.enable()


def create_iam_role(src_bucket, dest_bucket):
    import json
    json_data=json.loads('{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "s3.amazonaws.com"}, "Action": "sts:AssumeRole"}]}')
    role_name='newPythonReplicationRoleTestsAgainss'
    print(json.dumps(json_data))
    session = boto3.session.Session(profile_name='default')
    iam = session.client('iam')
    response = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(json_data),
    )
    role_permissions_policy=json.loads('{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:GetObjectVersionForReplication","s3:GetObjectVersionAcl","s3:GetObjectVersionTagging"],"Resource":["arn:aws:s3:::'+src_bucket+'/*"]},{"Effect":"Allow","Action":["s3:ListBucket","s3:GetReplicationConfiguration"],"Resource":["arn:aws:s3:::'+src_bucket+'"]},{"Effect":"Allow","Action":["s3:ReplicateObject","s3:ReplicateDelete","s3:ReplicateTags"],"Resource":"arn:aws:s3:::'+dest_bucket+'/*"}]}')
    print(json.dumps(role_permissions_policy))
    client = boto3.client('iam')
    response = client.put_role_policy(
        PolicyDocument=json.dumps(role_permissions_policy),
        PolicyName='replicationPythonRolePolicyTestsAgs',
        RoleName=role_name,
    )
    response=client.get_role(RoleName=role_name)
    arn = response['Role']['Arn']
    replication_config=json.loads('{"Role": "'+arn+'","Rules": [{"Status": "Enabled","Priority": 1,"DeleteMarkerReplication": { "Status": "Disabled" },"Filter" : { "Prefix": "Tax"},"Destination": {"Bucket": "arn:aws:s3:::'+dest_bucket+'"}}]}')
    client = boto3.client('s3')
    client.put_bucket_replication(Bucket=src_bucket, ReplicationConfiguration=replication_config)
    response = client.get_bucket_replication(Bucket=src_bucket)
    print(response)

def main():
    import argparse
   
    parser = argparse.ArgumentParser(description='Create 2 AWS S3 buckets <name>src and <name>dest a replication policy is created on bucket <name>src so everything that is added to this bucket is replicated to bucket <name>dest.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('bucket_name', help='This value is used as a prefix for the 2 AWS S3 buckets, the buckets are suffixed with "src" and "dest".')
    parser.add_argument('region', help="The region you want your S3 buckets to be created in.")
    args = parser.parse_args()

    create_1GB_file()
    
    bucket_name = args.bucket_name
    region=args.region
    
    s3_resource=get_s3(region)
    
    if(bucket_name and region):
        src_bucket = bucket_name +'src'
        dest_bucket = bucket_name + 'dest'
    elif not region and not bucket_name:
        print("Error: No region or bucket name was specified i.e. --bucket_name <name> --region <region>")
    elif not region:
        print("Error: No region was specified i.e. --region <region>")
    else:
        print("Error: No bucket name was specified i.e. --bucket_name <name>")

    create_bucket(src_bucket, region)
    create_bucket(dest_bucket, region)

    enable_version(src_bucket, s3_resource)
    enable_version(dest_bucket, s3_resource)
    
    filename=bucket_name+'-role-trust-policy.json'

    create_iam_role(src_bucket, dest_bucket)
    get_replica(src_bucket)


if __name__ == '__main__':
    main()
