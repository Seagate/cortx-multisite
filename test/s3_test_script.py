import boto3
import json
import os
import time

def get_s3(region=None):
    """

    Get a Boto 3 Amazon S3 resource with a specific AWS Region or with your
    default AWS Region.
    """
    return boto3.resource('s3', region_name=region) if region else boto3.resource('s3')

def delete_bucket(bucket):
    initial = False
    deleted=False

    s3 = boto3.resource('s3')
    buckets=[b.name for b in s3.buckets.all()]
    if bucket in buckets:
        initial = True
    else:
        print("Bucket does not exist")
        return False
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket)
    bucket.objects.all().delete()

    if bucket not in buckets:
        deleted=True
    else:
        print("delete bucket function did not work")
    return (deleted and initial)

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
    bucket=s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration=
        {
            'LocationConstraint': region
        }
    )
    return bucket

def delete_versioning(bucket, s3_resource):
    enabled=False
    client=boto3.client('s3')
    try:
        response = client.get_bucket_versioning(
            Bucket=bucket
        )
        if response['Status'] == 'Suspended':
            print("Versioning already disabled")
            return True
    except Exception:
        print("bucket versioning does not exist")
        return False
    versioning = s3_resource.BucketVersioning(bucket)
    versioning.suspend()
    
    try:
        response = client.get_bucket_versioning(
            Bucket=bucket
        )
        print(response['Status'])
        if response['Status'] == 'Suspended':
            enabled=True
            print("Versioning disabled")
    except Exception:
        print("deleting bucket versioning did not work")
    return enabled


def enable_versioning(bucket_name, s3_resource):
    enabled=False
    
    client=boto3.client('s3')
    try:
        response = client.get_bucket_versioning(
            Bucket=bucket_name
        )
        if response['Status'] == 'Enabled':
            print("Versioning already enabled")
            return True
    
    except Exception:
        print("bucket versioning does not exist")

    versioning = s3_resource.BucketVersioning(bucket_name)
    versioning.enable()
    
    try:
        response = client.get_bucket_versioning(
            Bucket=bucket_name
        )
        if response['Status'] == 'Enabled':
            enabled=True
            print("Versioning enabled")
    except Exception:
        print("bucket versioning did not work")
    return enabled


def create_iam_role(role_name):
    json_data=json.loads('{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "s3.amazonaws.com"},'\
    '"Action": "sts:AssumeRole"}]}')
    role_name=role_name

    session = boto3.session.Session(profile_name='default')
    iam = session.client('iam')
    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(json_data),
    )

def put_role_policy(role_name, policy_name, src_bucket, dest_bucket):

    role_permissions_policy=json.loads('{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:GetObjectVersionForReplication",'\
    '"s3:GetObjectVersionAcl","s3:GetObjectVersionTagging"],"Resource":["arn:aws:s3:::'+src_bucket+'/*"]},'\
    '{"Effect":"Allow","Action":["s3:ListBucket","s3:GetReplicationConfiguration"],"Resource":["arn:aws:s3:::'+src_bucket+'"]},'\
    '{"Effect":"Allow","Action":["s3:ReplicateObject","s3:ReplicateDelete","s3:ReplicateTags"],"Resource":"arn:aws:s3:::'+dest_bucket+'/*"}]}')

    client = boto3.client('iam')
    response = client.put_role_policy(
        PolicyDocument=json.dumps(role_permissions_policy),
        PolicyName=policy_name,
        RoleName=role_name,
    )
    response=client.get_role(RoleName=role_name)
    arn = response['Role']['Arn']
    replication_config=json.loads('{"Role": "'+arn+'","Rules": [{"Status": "Enabled","Priority": 1,"DeleteMarkerReplication": { "Status": "Disabled" },'\
    '"Filter" : { "Prefix": "Tax"},"Destination": {"Bucket": "arn:aws:s3:::'+dest_bucket+'"}}]}')
    client = boto3.client('s3')
    client.put_bucket_replication(Bucket=src_bucket, ReplicationConfiguration=replication_config)

def create_file():
    filename="sample.txt"
    fp = open('sample.txt', 'w')
    fp.write('sample text')
    fp.close()
    return filename

def is_data_equal(src_bucket, dest_bucket):
    s3 = boto3.resource('s3')

    src_bucket = s3.Bucket(src_bucket)
    dest_bucket = s3.Bucket(dest_bucket)
        
    src_key=[]
    src_body=[]
    for obj in src_bucket.objects.all():
        src_key.append(obj.key)
        src_body.append(obj.get()['Body'].read())

    time.sleep(300)

    dest_key=[]
    dest_body=[]
    for obj in dest_bucket.objects.all():
        dest_key.append(obj.key)
        dest_body.append(obj.get()['Body'].read())
    
    if dest_key != src_key:
        print("Replication does not copy the key value as expected: src_key=" + str(src_key) + " and dest_key="+ str(dest_key))
    elif dest_body != src_body:
        print("Replication does not copy the object body as expected: src_body=" + str(src_body) + " and dest_body="+ str(dest_body))
    return ((dest_key == src_key) and (dest_body == src_body))


def add_data(file_name, bucket_name):
    s3_client = boto3.client('s3')
    s3_client.upload_file(file_name, bucket_name, "Tax/test")


def does_replication_policy_exist(src_bucket):
    client=boto3.client('s3')
    try:
        response = client.get_bucket_replication(Bucket=src_bucket)
        response=(response['ResponseMetadata'])['HTTPStatusCode']
    except Exception:
        print("Replication policy does not exist for this bucket")
        return False
    return (200 == response)

def create_replication_policy(bucket_name, region, role_name, policy_name):
    src_bucket = bucket_name+'src'
    dest_bucket = bucket_name+'dest'
     
    create_bucket(src_bucket, region)
    enable_versioning(src_bucket, get_s3(region))
    
    create_bucket(dest_bucket, region)
    enable_versioning(dest_bucket, get_s3(region))

    create_iam_role(role_name)
    put_role_policy(role_name, policy_name, src_bucket, dest_bucket)
    client = boto3.client('iam')
    response=client.get_role(RoleName=role_name)
    arn = response['Role']['Arn']
    replication_config=json.loads('{"Role": "'+arn+'","Rules": [{"Status": "Enabled","Priority": 1,"DeleteMarkerReplication": '\
    '{ "Status": "Disabled" },"Filter" : { "Prefix": "Tax"},"Destination": {"Bucket": "arn:aws:s3:::'+dest_bucket+'"}}]}')
    
    return replication_config

def does_replication_policy_create_folder_in_bucket(replication_config, src_bucket, dest_bucket):
    # replication policy exists
    client=boto3.client('s3')
    client.put_bucket_replication(Bucket=src_bucket, ReplicationConfiguration=replication_config)
    time.sleep(100)

    if(does_replication_policy_exist(src_bucket)):
        print("replication exists")
        # Check that data is the same when replicated data is added to source
        file_name=create_file()
        add_data(file_name, src_bucket)
        data_equal=is_data_equal(src_bucket,dest_bucket)
        return data_equal
    else:
        print("Replication policy does not create folder as expected")
        return False

def verbose(verbose, prompt, message):
    if not verbose:
        return

    # Commenting out due to codecy issue
    # Commenting out doesn't seem to make any impact on code flow
    # create_iam_role(src_bucket, dest_bucket)
    
    print("About to create bucket %s" % message)
    input("Press Enter to continue")
    return

def replication_policy_exists(bucket):
    client = boto3.client('s3')
    try:
        response = client.get_bucket_replication(Bucket=bucket)
        http_status_code = (response['ResponseMetadata'])['HTTPStatusCode']
        return (http_status_code == 200)
    except Exception:
        print("Bucket policy does not exist")
        return False

def delete_replication_policy(bucket):
    client = boto3.client('s3')
    print(client.get_bucket_replication(Bucket=bucket))
    try:
        response = client.get_bucket_replication(Bucket=bucket)
        http_status_code = (response['ResponseMetadata'])['HTTPStatusCode']
    except Exception:
        print("Bucket does not have a policy")
        return False

    response = client.delete_bucket_replication(
        Bucket=bucket
    )
    http_status_code = (response['ResponseMetadata'])['HTTPStatusCode']
    
    try:
        response = client.get_bucket_replication(Bucket=bucket)
        http_status_code = (response['ResponseMetadata'])['HTTPStatusCode']
        print("Replication policy does exist but could not delete replication policy")
        return False
    except Exception:
        print("Replication policy has been deleted")

    return http_status_code == 204

def print_result(header, result):
    print(header, "-", result)


def do_test(header, bucket_name=None, region=None, role_name=None, policy_name=None):

    if header=='replication_policy_exists':
        response = create_replication_policy(bucket_name, region, role_name, policy_name)
        result = (200 == ((response['ResponseMetadata'])['HTTPStatusCode']))
        print_result(header, result)

        return (200 == ((response['ResponseMetadata'])['HTTPStatusCode']))
    elif header == 'create_bucket':
        bucket = create_bucket(bucket_name, region)
        result=(bucket_name == bucket.name)
        print_result(header, result)
        return (bucket_name == bucket.name)
    elif header == 'delete_replication_policy':
        result=delete_replication_policy(bucket_name)
        print_result(header, result)
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
        print("This test will create a bucket and call the buckets name to make sure the bucket exists")
        bucket_name=str(input("Enter a bucket name: "))
        region=str(input("Enter a valid region: "))
        result = do_test(header, bucket_name, region)
        print_result(header, result)
    elif header == 'replication_policy_exists':
        print("This test will create a bucket 2 buckets 1 bucket will be called <bucket_name>src \
                and the other <bucket_name>dest. Then there will be a replication policy created \
                which replicates all data written to the folder 'Tax' in <bucket_name>src asynchronously to <bucket_name>dest")
        print("Press Enter if you would wish to proceed. Otherwise enter another test name. The tests are listed below:")
        print_choices()
        input()
        bucket_name=str(input("Enter a bucket name: "))
        region=str(input("Enter a valid region: "))
        role_name=str(input("Enter a name for your iam role: "))
        policy_name=str(input("Enter a name for your iam policy: "))
        result = do_test(header, bucket_name, region, role_name, policy_name)
        print_result(header, result)
    elif header == 'delete_replication_policy':
        bucket_name=str(input("Enter a bucket name: "))
        result = do_test(header, bucket_name)
        print_result(header, result)

def auto():
    rand_int=str(ord(os.urandom(1)))

    bucket_name='adgtest'+rand_int
    src_bucket=bucket_name+'src'
    dest_bucket=bucket_name+'dest'
    region='us-west-2'
    role_name='adgtestrole'+rand_int
    policy_name='adgpolicy'+rand_int
   
    replication_config = create_replication_policy(bucket_name, region, role_name, policy_name)
    
    result = does_replication_policy_create_folder_in_bucket(replication_config, src_bucket, dest_bucket)
    print_result("does_replication_policy_create_folder_in_bucket", result)

    result=replication_policy_exists(src_bucket)
    print_result('replication_policy_exists', result)

    result = delete_bucket('adgtest35src')
    print_result("delete_bucket", result)
    
    result=delete_replication_policy(src_bucket)
    print_result('delete_replication_policy', result)
    
    result=delete_versioning(src_bucket, get_s3(region))
    print_result('delete_versioning', result)

    result = enable_versioning(src_bucket, get_s3(region))
    print_result('enable_versioning', result)
  
def main():
    auto()
    #prompt()
    

if __name__ == '__main__':
    main()
