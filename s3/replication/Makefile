# Makefile for static analysis and formatting fix

PYTHON_SCRIPTS :=

# By default, search for --filename=*.py
# Add --exit-zero to ignore flake8 exit status
FLAKE8_OPTS :=
AUTOPEP8_OPTS := --in-place --aggressive --aggressive --recursive

check: flake8

flake8:
	cd common; make flake8; cd ..
	cd manager; make flake8; cd ..
	cd replicator; make flake8; cd ..

autopep8:
	autopep8 $(AUTOPEP8_OPTS) common manager replicator

clean:
	cd common; make clean; cd ..
	cd manager; make clean; cd ..
	cd replicator; make clean; cd ..

install:
	cd common; make install; cd ..
	cd manager; make install; cd ..
	cd replicator; make install; cd ..

test: check
	cd common; make test; cd ..
	cd manager; make test; cd ..
	cd replicator; make test; cd ..
