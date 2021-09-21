# Introduction
Common modules for CORTX cross cluster/region replication for S3 objects.

## Modules
Following modules are defined in common package to be used by replication manager and replicator.

## Logging
TBD

## Job module used across replication manager and replicator
TBD

## Quickstart

Create a virtualenv.
```sh
python3 -m venv s3env
```

Activate virtualenv s3env.
```sh
source s3env/bin/activate
```

Install dependencies in active virtualenv.
```sh
pip3 install -r requirements.txt
```

Clean earlier install.
```sh
python3 setup.py clean --all
```

Install the package.
```sh
python3 setup.py install
```

Executing Tests.
First update the configuration to point to your CORTX s3 setup. Create file `~/.cortxs3/credentials.yaml` with `access_key` and `secret_key` relevant for your S3 setup.
For running tests against aws update the configuration to point to your aws s3. Create file `~/.aws/credentials` with `access_key` and `secret_key` relevant for your S3 setup.
For some tests 'aws cli' installation is also required for now. aws s3api is used to do some setup before running some tests.(e.g. get-bucket-replication) as api development will take place there will not be further need to do bucket or object related setup via aws s3api.
If user wants to run tests for aws endpoint, then one has to pass `TARGET=aws`.
Before running `make test` be sure to provide right config options in ./tests/system/config/config.yaml file.


***Note: DO NOT accidently commit/checkin your access_key/secret_key***

```sh
make clean
make install
make test or  make test TARGET=aws
```
