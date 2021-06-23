# Introduction

Replication manager for CORTX cross cluster/region replication for S3 objects.

## Description

This module performs following:
1.  Receive "replication jobs" i.e FDMI records on S3 object create or S3 Object tag updates. FDMI records contain S3 metadata entries.
2.  Persist replication jobs in distributed Motr KVS. (Queue)
3.  Distribute jobs to subscribers.
4.  Updates S3 metadata to reflect replication status once jobs are acknowledged by subscribers.
5.  Maintain a list of inprogress jobs and queued jobs and return on query.

## Quickstart

Create a virtualenv.
```sh
python3 -m venv s3env
```

Activate virtualenv s3env.
```sh
source s3env/bin/activate
```

Clean earlier install.
```sh
python3 setup.py clean --all
```

Install dependencies in active virtualenv.
```sh
pip3 install -r requirements.txt
```

Install the development/test dependencies from devel-requirements.txt
```sh
pip3 install  -e .[development]
```

Install the package.
```sh
python3 setup.py install
```

Replication manager currently provides ability to define target sites using
following config files. These files needs to be updated to point to your test
target sites. This is eventually be replaced using Bucket replication configuration
from S3 server.

Files to be modified.
`~/.cortxs3/cortx_s3.yaml` and `~/.cortxs3/aws_s3.yaml`
These can also be modified in source or use reference from source from
`manager/src/config/` folder.

Start the replicator.
```sh
python3 -m s3replicationmanager
```

Following sections specify how to test replication manager.
Tests use some sample data, and one of the files used is
`manager/tests/system/data/fdmi_test_job.json`

Modify appropriate values to run a specific test. Most attributes are
self explanatory. But `x-amz-meta-target-site` takes 2 different values
as `cortxs3` for cortx target and `awss3` for aws s3 target.

Run system tests after starting the Replication manager.
```sh
py.test tests/system
```

To run individual test group.
```sh
py.test tests/system/test_subscribers_resource.py
py.test tests/system/test_jobs_resource.py
```

To run specific test.
```sh
py.test tests/system -k 'test_post_job[valid_job-201]'
py.test tests/system -k 'test_post_subscriber[valid_payload-201]'
```

For testing with cortx s3, following user defined attributes can be specified
to simulate replication events.
```sh
s3cmd put --add-header x-amz-meta-replication:true \
          --add-header x-amz-meta-target-site:awss3 \
          --add-header x-amz-meta-target-bucket:targetbucket \
          someobject.jpg s3://sourcebucket
```
