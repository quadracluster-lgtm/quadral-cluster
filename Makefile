.PHONY: setup run test lint typecheck fmt

VENV?=.venv
PY?=$(VENV)/bin/python
PIP?=$(VENV)/bin/pip

setup:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]

run:
	$(VENV)/bin/uvicorn src.quadral_cluster.main:app --host 0.0.0.0 --port 8000 --reload

test:
	$(VENV)/bin/pytest -q

lint:
	$(VENV)/bin/ruff check .

fmt:
	$(VENV)/bin/ruff check . --fix

typecheck:
	$(VENV)/bin/mypy src
