# Introduction

Replication manager for CORTX cross cluster/region replication for S3 objects.

# Description

This module performs following
1. Receive "replication jobs" i.e FDMI records on S3 object create or S3 Object tag updates. FDMI records contain S3 metadata entries.
2. Persist replication jobs in distributed Motr KVS. (Queue)
3. Distribute jobs to subscribers.
4. Updates S3 metadata to reflect replication status once jobs are acknowledged by subscribers.
5. Maintain a list of inprogress jobs and queued jobs and return on query.

# Quickstart

Create a virtualenv.
```sh
$ python3 -m venv s3env
```

Activate virtualenv s3env.
```sh
$ source s3env/bin/activate
```

Clean earlier install.
```sh
python3 setup.py clean --all
```

Install dependencies in active virtualenv.
```sh
$ pip3 install -r requirements.txt
```

Install the development/test dependencies from devel-requirements.txt
```sh
pip3 install  -e .[development]
```

Install the package.
```sh
$ python3 setup.py install
```

Start the replicator.
```sh
$ python3 -m s3replicationmanager
```

Run system tests after starting the replicator.
```sh
$ python3 manager/tests/system/manager_client.py
```