# Introduction

Replicator for CORTX cross cluster/region replication for S3 objects.

# Description

This module performs following
1. Receive "replication jobs" from replication manager.
2. Perform the replication
3. Acknowledge the replication jobs to replication manager.
4. Main a list of inprogress jobs and return on query.

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
$ python3 -m s3replicator
