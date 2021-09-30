import sys
import boto3
from botocore.exceptions import ClientError
import json
import os
import argparse

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
    return bucket
    #enable_versioning(bucket_name, s3)


def enable_versioning(bucket_name, s3_resource):
    versioning = s3_resource.BucketVersioning(bucket_name)
    versioning.enable()


def create_iam_role(role_name):
    json_data=json.loads('{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "s3.amazonaws.com"}, "Action": "sts:AssumeRole"}]}')

    session = boto3.session.Session(profile_name='default')
    iam = session.client('iam')
    response = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(json_data),
    )

def put_role_policy(role_name, policy_name, src_bucket, dest_bucket):
    role_permissions_policy=json.loads('{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:GetObjectVersionForReplication","s3:GetObjectVersionAcl","s3:GetObjectVersionTagging"],"Resource":["arn:aws:s3:::'+src_bucket+'/*"]},{"Effect":"Allow","Action":["s3:ListBucket","s3:GetReplicationConfiguration"],"Resource":["arn:aws:s3:::'+src_bucket+'"]},{"Effect":"Allow","Action":["s3:ReplicateObject","s3:ReplicateDelete","s3:ReplicateTags"],"Resource":"arn:aws:s3:::'+dest_bucket+'/*"}]}')
    
    client = boto3.client('iam')
    response = client.put_role_policy(
        PolicyDocument=json.dumps(role_permissions_policy),
        PolicyName='replicationPythonRolePolicyTestsAgs',
        RoleName=role_name,
    )


def create_replication_policy(src_bucket, dest_bucket, role_name, policy_name):
    create_iam_role(role_name)
    put_role_policy(role_name, policy_name, src_bucket, dest_bucket)
    client = boto3.client('iam')
    response=client.get_role(RoleName=role_name)
    arn = response['Role']['Arn']
    replication_config=json.loads('{"Role": "'+arn+'","Rules": [{"Status": "Enabled","Priority": 1,"DeleteMarkerReplication": { "Status": "Disabled" },"Filter" : { "Prefix": "Tax"},"Destination": {"Bucket": "arn:aws:s3:::'+dest_bucket+'"}}]}')
    client = boto3.client('s3')
    client.put_bucket_replication(Bucket=src_bucket, ReplicationConfiguration=replication_config)
    response = client.get_bucket_replication(Bucket=src_bucket)
    return response

def verbose(verbose, prompt, message):
    if not verbose:
        return

    print("About to create bucket %s" % message)
    input("Press Enter to continue")
    return

def delete_replication_policy(src_bucket):
    client = boto3.client('s3')
    print(src_bucket)
    response = client.get_bucket_replication(Bucket=src_bucket)
    http_status_code = (response['ResponseMetadata'])['HTTPStatusCode']
    if http_status_code != 200:
        return "Error this bucket does not have a replication policy"
    response = client.delete_bucket_replication(
        Bucket=src_bucket
    )
    http_status_code = (response['ResponseMetadata'])['HTTPStatusCode']
    try:
        response = client.get_bucket_replication(Bucket=src_bucket)
        http_status_code = (response['ResponseMetadata'])['HTTPStatusCode']
    except:
        print("Replication policy has been deleted")
    return response == 204


def do_test(header, bucket_name, region, role_name, policy_name):
    if(bucket_name and region):
        src_bucket = bucket_name +'src'
        dest_bucket = bucket_name + 'dest'
    elif not region and not bucket_name:
        print("Error: No region or bucket name was specified i.e. --bucket_name <name> --region <region>")
    elif not region:
        print("Error: No region was specified i.e. --region <region>")
    else:
        print("Error: No bucket name was specified i.e. --bucket_name <name>")
        
    if header=='replication_policy_exists':
        create_bucket(src_bucket, region)
        enable_versioning(src_bucket, get_s3(region))
        
        create_bucket(dest_bucket, region)
        enable_versioning(dest_bucket, get_s3(region))
        
        response = create_replication_policy(src_bucket, dest_bucket, role_name, policy_name)
        
        return (200 == ((response['ResponseMetadata'])['HTTPStatusCode']))
    elif header == 'create_bucket':
        bucket = create_bucket(bucket_name, region)
        return (bucket_name == bucket.name)
    elif header == 'delete_replication_policy':
        return delete_replication_policy(src_bucket)


def main():
       
    parser = argparse.ArgumentParser(description='Creates 2 S3 buckets <name>src and <name>dest a replication policy is created on bucket <name>src so everything that is added to this bucket is replicated to bucket <name>dest.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('bucket_name', help='This value is used as a prefix for the 2 S3 buckets, the buckets are suffixed with "src" and "dest".')
    parser.add_argument('region', help="The region you want your S3 buckets to be created in.")
    parser.add_argument('--verbose', '-v', help='displays verbose output', action='store_false')
    parser.add_argument('--prompt', '-p', help='Provides the user with a prompt message before each test', action='store_true')
    parser.add_argument('header', choices=['replication_policy_exists', 'create_bucket', 'delete_replication_policy'], help='the s3 header for the s3 call you wish to make')
    
    parser.add_argument('role_name', help='the name of the aws iam role you want to create')
    parser.add_argument('policy_name', help='The name of the replication policy you are creating')

    args = parser.parse_args()
    
    #create_1GB_file()
    
    bucket_name = args.bucket_name
    region=args.region

    verbose(args.verbose, args.prompt, bucket_name)
    
    header=args.header
    role_name=args.role_name
    policy_name=args.policy_name

    print(do_test(header, bucket_name, region, role_name, policy_name))
    #create_bucket(src_bucket, region)
    #create_bucket(dest_bucket, region)

    #create_replication_policy(src_bucket, dest_bucket, args.role_name, args.policy_name)


if __name__ == '__main__':
    main()
