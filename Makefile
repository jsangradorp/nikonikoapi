PYTHON_MODULES := nikoniko
PYTHONPATH := .:./nikoniko
TESTSPATH := ./tests
VENV := .venv
PYTEST := env PYTHONPATH=$(PYTHONPATH) PYTEST=1 $(VENV)/bin/py.test --cov=$(PYTHON_MODULES) --cov-report=html -v
PYLINT := env PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/pylint --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"
PEP8 := env PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/pep8 --repeat
PYTHON := env PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/python
PIP := $(VENV)/bin/pip
JWT_SECRET_KEY := fake-secret-key
export JWT_SECRET_KEY

DEFAULT_PYTHON := /usr/local/bin/python3
VIRTUALENV := /usr/local/bin/virtualenv

REQUIREMENTS := -r requirements.txt

default: check-coding-style

venv:
	test -d $(VENV) || $(VIRTUALENV) -p $(DEFAULT_PYTHON) -q $(VENV)
requirements:
	@if [ -d wheelhouse ]; then \
	        $(PIP) install -q --no-index --find-links=wheelhouse $(REQUIREMENTS); \
	else \
	        $(PIP) install -q $(REQUIREMENTS); \
	fi
bootstrap: venv requirements

check-coding-style: bootstrap
	$(PEP8) $(PYTHON_MODULES) $(TESTSPATH)
	$(PYLINT) -E $(PYTHON_MODULES)
pylint-full: check-coding-style
	$(PYLINT) $(PYTHON_MODULES) $(TESTSPATH)
check:
	$(PYTEST) $(TESTSPATH)
test: check-coding-style check

.PHONY: default venv requirements bootstrap check-coding-style pylint-full test check
