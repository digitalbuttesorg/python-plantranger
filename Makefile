VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

.PHONY: setup test clean

## setup: create the virtualenv and install the library with its test tools
setup: $(VENV)/.installed

$(VENV)/.installed: requirements-test.txt pyproject.toml
	rm -rf $(VENV)
	python3 -m venv $(VENV) 2>/dev/null || virtualenv -p python3 $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-test.txt -e .
	touch $(VENV)/.installed

## test: run the test suite (installs deps first if needed)
test: setup
	$(PY) -m pytest

## clean: remove the virtualenv and test caches
clean:
	rm -rf $(VENV) .pytest_cache
