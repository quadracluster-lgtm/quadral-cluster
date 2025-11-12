from __future__ import annotations

import os
import sys
import tempfile
import contextlib
import typing as t
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@contextlib.contextmanager
def _temp_sqlite_url() -> t.Iterator[str]:
    fd, path = tempfile.mkstemp(prefix="qc_test_", suffix=".db")
    os.close(fd)
    try:
        yield f"sqlite:///{path}"
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


@pytest.fixture(scope="session")
def test_client() -> t.Iterator[TestClient]:
    """
    Создаёт временную SQLite-БД, добавляет src в sys.path,
    импортирует FastAPI app и отдаёт TestClient.
    """
    # 1) Тестовая БД
    with _temp_sqlite_url() as url:
        os.environ["DATABASE_URL"] = url

        # 2) Путь к src/
        repo_root = Path(__file__).resolve().parents[1]
        src_path = repo_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        # 3) Импорт после подготовки окружения
        from quadral_cluster.main import app  # type: ignore

        # 4) Создать схему, если экспортированы Base/engine
        try:
            from quadral_cluster.database import Base, engine  # type: ignore
            Base.metadata.create_all(bind=engine)  # noqa: PIE804
        except Exception:
            pass

        with TestClient(app) as client:
            yield client
