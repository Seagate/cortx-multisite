# Introduction

This section describes common content for various modules in this project. See individual module readme for more details.

## Quickstart

Ensure you have latest pip installed.

```sh
python3 -m pip install --upgrade pip
```

Perform flake8 checks on the python code.
```sh
make check
```
or 
```sh
make flake8
```

Autocorrect formatting errors for flake8.
```sh
make autopep8
```

Run basic tests for each module. Clean, Build and test.
```sh
make test
```

## Troubleshooting
When running `make test` on MacOS, timeout in Makefile may fail and you need following.

```sh
brew install coreutils
sudo ln -s /usr/local/bin/gtimeout /usr/local/bin/timeout
export PATH=$PATH:/usr/local/bin/
```

Additionally MacOS returns non-zero error code without timeout even with --preserve-status, so you may want to for now manually test last 2 steps in make test. Will be fixed soon.
```sh
python3 -m s3replicationmanager
# Server should be started. Press CTRL+C to quit
python3 -m s3replicator
# Server should be started. Press CTRL+C to quit
```