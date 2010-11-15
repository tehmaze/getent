PYTHON=/usr/bin/env python
PYTHONPATH=$(shell pwd)

all: build

build: .FORCE
	$(PYTHON) setup.py build

install: .FORCE
	$(PYTHON) setup.py install

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) getent/__init__.py

.FORCE:

