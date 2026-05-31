.PHONY: install install-dev lint test run demo

VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install -r requirements-dev.txt

lint:
	$(VENV)/bin/ruff check backend tests
	$(VENV)/bin/ruff format --check backend tests

format:
	$(VENV)/bin/ruff format backend tests
	$(VENV)/bin/ruff check --fix backend tests

test:
	PYTHONPATH=. DEMO_MODE=true $(VENV)/bin/pytest -q

run:
	PYTHONPATH=. $(VENV)/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --reload

demo:
	PYTHONPATH=. DEMO_MODE=true $(VENV)/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
