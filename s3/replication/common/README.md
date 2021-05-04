# Introduction
Common modules for CORTX cross cluster/region replication for S3 objects.

# Modules
Following modules are defined in common package to be used by replication manager and replicator.

## Logging
TBD

## Job module used across replication manager and replicator
TBD

# Quickstart

Create a virtualenv.
```sh
$ python3 -m venv s3env
```

Activate virtualenv s3env.
```sh
$ source s3env/bin/activate
```

Install dependencies in active virtualenv.
```sh
$ pip3 install -r requirements.txt
```

Clean earlier install.
```sh
python3 setup.py clean --all
```

Install the package.
```sh
$ python3 setup.py install
```