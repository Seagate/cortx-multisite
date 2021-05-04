PYTHON  := python3.6
PIP     := pip3
SHELL   := bash

PYTHON_SCRIPTS :=
FLAKE8_OPTS := --filename=*.py

check: flake8
    @echo "inside check"

flake8:
    @echo "inside flake8" 
    flake8 $(FLAKE8_OPTS) $^

install-deps: requirements.txt
    @echo "inside install-deps"
    pip3 install -r requirements.txt
