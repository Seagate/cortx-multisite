# Makefile for static analysis and formatting fix

PYTHON_SCRIPTS :=

# By default, search for --filename=*.py
# Add --exit-zero to ignore flake8 exit status
FLAKE8_OPTS :=
AUTOPEP8_OPTS := --in-place --aggressive --aggressive --recursive 

check: flake8

flake8: */src/**/*.py */test/*.py
	flake8 $(FLAKE8_OPTS) $^

autopep8:
	autopep8 $(AUTOPEP8_OPTS) common manager replicator

test: check
  # Quick run for build and test.
	# Deactivate any old virtualenv and create new one, activate
	deactivate | true
	python3 -m venv s3env; source s3env/bin/activate
	# For each package, clean, build and test.
	# Clean all
	cd common && python3 setup.py clean --all ; cd .. \
	cd manager ; python3 setup.py clean --all ; cd .. \
	cd replicator ; python3 setup.py clean --all ; cd .. \
	# Build and test
	cd common && python3 setup.py install && cd ..
	# Test s3replicationmanager.
	cd manager && pip3 install  -e .[development] && \
	python3 setup.py install && \
	timeout --preserve-status 1s python3 -m s3replicationmanager && cd ..
	# Test s3replicator.
	cd replicator && pip3 install  -e .[development] && \
	python3 setup.py install && \
	timeout --preserve-status 1s python3 -m s3replicator && cd ..
	deactivate | true