.PHONY: dev run test lint fmt

dev:
	pip install -e .[dev]

run:
	uvicorn src.quadral_cluster.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest

lint:
	ruff check .

fmt:
	ruff check . --fix
