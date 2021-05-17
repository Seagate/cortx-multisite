# Makefile for static analysis and formatting fix

PYTHON_SCRIPTS :=

# By default, search for --filename=*.py
# Add --exit-zero to ignore flake8 exit status
FLAKE8_OPTS :=
AUTOPEP8_OPTS := --in-place --aggressive --aggressive --recursive

check: flake8

flake8: src/**/*.py tests/**/*.py
	flake8 $(FLAKE8_OPTS) $^

autopep8:
	autopep8 $(AUTOPEP8_OPTS) src tests

setups3env:
	python3 -m venv ../s3env; source ../s3env/bin/activate

clean:
	python3 setup.py clean --all

install: setups3env
	pip3 install  -e .[development]
	python3 setup.py install

test: install
	timeout --preserve-status 1s python3 -m s3replicator