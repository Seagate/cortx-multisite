# Introduction

Replication manager for CORTX cross cluster/region replication for S3 objects.

# Description

This module performs following
1. Receive "replication jobs" i.e FDMI records on S3 object create or S3 Object tag updates. FDMI records contain S3 metadata entries.
2. Persist replication jobs in distributed Motr KVS. (Queue)
3. Distribute jobs to subscribers.
4. Updates S3 metadata to reflect replication status once jobs are acknowledged by subscribers.
5. Main a list of inprogress jobs and queued jobs and return on query.

# Quickstart

Create a virtualenv.
$ python3 -m venv s3env

Activate virtualenv s3env.
$ source s3env/bin/activate

Install dependencies in active virtualenv.
$ pip3 install -r requirements.txt

Clean earlier install.
python3 setup.py clean --all

Install the package.
$ python3 setup.py install

Start the replicator.
$ python3 -m s3replicationmanager
