# Makefile for static analysis and formatting fix

PYTHON_SCRIPTS :=

.PHONEY: tests

# By default, search for --filename=*.py
# Add --exit-zero to ignore flake8 exit status
FLAKE8_OPTS :=
AUTOPEP8_OPTS := --in-place --aggressive --aggressive --recursive
TARGET :=

check: flake8

flake8: src/**/*.py tests/**/*.py
	python3 -m flake8 $(FLAKE8_OPTS) $^

autopep8:
	python3 -m autopep8 $(AUTOPEP8_OPTS) src tests

clean:
	python3 setup.py clean --all

install:
	pip3 install  -e .[development]
	python3 setup.py install


test: common_tests aws_supported_tests
	@(printf "\nAll tests done!\n")

common_tests:
	@(printf "\n\nRunning tests...\n")
	@(printf "_________________\n")
	@(printf "\n\nTest case: Create test object\n")
	python tests/system/test_put_object.py
	@(printf "\n\nTest case: Reads test object\n")
	python tests/system/test_get_object.py
	@(printf "\n\nTest case: Reads test head object\n")
	python tests/system/test_head_object.py
	@(printf "\n\nTest case: Create test object tag\n")
	python tests/system/test_put_object_tagging.py
	@(printf "\n\nTest case: Reads test object tag\n")
	python tests/system/test_get_object_tagging.py
	@(printf "\n\nTest case: Transfers test object\n")
	python tests/system/s3_async_transfer_object.py
	@(printf "\n\nTest case: Multipart upload\n")
	python tests/system/test_multipart_upload.py

ifeq ($(TARGET), aws)
aws_supported_tests:
	@(printf "\naws supported tests...\n")
	@(printf "________________________\n")
	@(printf "\n\nTest case: put bucket replication\n")
	python tests/system/test_put_bucket_replication.py
	@(printf "\n\nTest case: get bucket replication\n")
	python tests/system/test_get_bucket_replication.py
else
aws_supported_tests:
endif
