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
    try:
        response = client.get_bucket_replication(Bucket=src_bucket)
        http_status_code = (response['ResponseMetadata'])['HTTPStatusCode']
    except:
        print("Bucket policy does not exist")
        return False

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


def do_test(header, bucket_name=None, region=None, role_name=None, policy_name=None):
        
    if header=='replication_policy_exists':
        src_bucket = bucket_name+'src'
        dest_bucket = bucket_name+'dest'
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
        return delete_replication_policy(bucket_name)

def print_choices():
    choices=['replication_policy_exists', 'create_bucket', 'delete_replication_policy']
    print("Please select a test you would like to do by entering the test header below:")
    for i in choices:
        print("\n- " + i)
    print("\n")


def prompt():
    print("Please select a test you would like to do by entering the test header below:")
    print_choices()
    header=str(input("Enter test name:\n"))
    if header == 'create_bucket':
        bucket_name=str(input("Enter a bucket name: "))
        region=str(input("Enter a valid region: "))
        print(bucket_name, region)
        #do_test(header, bucket_name, region)
    elif header == 'replication_policy_exists':
        print("This test will create a bucket 2 buckets 1 bucket will be called <bucket_name>src and the other <bucket_name>dest. Then there will be a replication policy created which replicates all data written to the folder 'Tax' in <bucket_name>src asynchronously to <bucket_name>dest")
        print("Press Enter if you would wish to proceed. Otherwise enter another test name. The tests are listed below:")
        print_choices()
        input()
        bucket_name=str(input("Enter a bucket name: "))
        region=str(input("Enter a valid region: "))
        role_name=str(input("Enter a name for your iam role: "))
        policy_name=str(input("Enter a name for your iam policy: "))
        do_test(header, bucket_name, region, role_name, policy_name)
    elif header == 'delete_replication_policy':
        bucket_name=str(input("Enter a bucket name: "))
        do_test(header, bucket_name)

def main():
    
    prompt()

if __name__ == '__main__':
    main()
