# Makefile for static analysis and formatting fix

PYTHON_SCRIPTS :=
FLAKE8_OPTS := --exit-zero # By default search for --filename=*.py 
AUTOPEP8_OPTS := --in-place --aggressive --aggressive --recursive 

check: flake8

flake8: */src/**/*.py */test/*.py
	flake8 $(FLAKE8_OPTS) $^

autopep8:
	autopep8 $(AUTOPEP8_OPTS) common manager replicator
