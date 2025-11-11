.PHONY: dev run test lint fmt

dev:
	python -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -e .[dev] || pip install -e . && pip install pytest httpx ruff

run:
	. .venv/bin/activate && uvicorn src.quadral_cluster.main:app --host 0.0.0.0 --port 8000 --reload

test:
	. .venv/bin/activate && pytest -q

lint:
	. .venv/bin/activate && ruff check .

fmt:
	. .venv/bin/activate && ruff check . --fix
