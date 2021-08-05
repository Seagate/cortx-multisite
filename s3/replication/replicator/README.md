# Introduction

Replicator for CORTX cross cluster/region replication for S3 objects.

## Description

This module performs following
1.  Receive "replication jobs" from replication manager.
2.  Perform the replication
3.  Acknowledge the replication jobs to replication manager.
4.  Maintain a list of inprogress jobs and return on query.

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

Start the replicator.
```sh
python3 -m s3replicator
```

Run simple system tests.
```sh
py.test tests/system/test_replicator.py -v
```

Run load transfer tests.
```sh
python3 tests/system/load_transfer_test.py
```

## Configurations

Number of connections should be greater than count of replications run
in parallel, and ideally it should be twice.
In replicator config.yaml, its recommended to have
max_connections_per_s3_session = 2 * max_replications
