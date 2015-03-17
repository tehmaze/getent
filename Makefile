PYTHON=/usr/bin/env python
PYTHONPATH=$(shell pwd)

all: build

build: .FORCE
	$(PYTHON) setup.py build

install: .FORCE
	$(PYTHON) setup.py install

lint:
	(pep8   --help > /dev/null) && pep8 -v getent
	(pep257 --help > /dev/null) && pep257 getent
	(flake8 --help > /dev/null) && flake8 -v getent

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) getent/__init__.py

.FORCE:

