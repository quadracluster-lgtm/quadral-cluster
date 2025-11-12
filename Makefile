PY ?= python3.12

.PHONY: dev run test lint fmt

dev:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]" || $(PY) -m pip install -e .
	$(PY) -m pip install pytest ruff

run:
	uvicorn quadral_cluster.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest -q

lint:
	ruff check .

fmt:
	ruff check . --fix
