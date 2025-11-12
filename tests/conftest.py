from __future__ import annotations

import os
import tempfile
import contextlib
import typing as t

import pytest
from fastapi.testclient import TestClient


@contextlib.contextmanager
def _temp_sqlite_url() -> t.Iterator[str]:
    fd, path = tempfile.mkstemp(prefix="qc_test_", suffix=".db")
    os.close(fd)
    try:
        yield f"sqlite:///{path}"
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.remove(path)


@pytest.fixture(scope="session")
def test_client() -> t.Iterator[TestClient]:
    """
    Создаёт временную SQLite-БД, поднимает FastAPI app и отдаёт TestClient.
    ВАЖНО: импорт приложения и database — после установки env.
    """
    with _temp_sqlite_url() as url:
        os.environ["DATABASE_URL"] = url

        # Импорты после установки env: не нарушаем Ruff E402
        from src.quadral_cluster.main import app  # type: ignore

        try:
            from src.quadral_cluster.database import Base, engine  # type: ignore
            Base.metadata.create_all(bind=engine)  # noqa: PIE804
        except Exception:
            pass

        with TestClient(app) as client:
            yield client
