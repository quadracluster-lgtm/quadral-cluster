from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


# SQLAlchemy Base (v2)
class Base(DeclarativeBase):
    pass


# Settings
settings = get_settings()

# Engine (SQLite по умолчанию, см. config.py)
engine = create_engine(
    settings.database_url,  # например: "sqlite:///./dev.db"
    future=True,
    echo=False,
)

# Фабрика сессий
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


# FastAPI dependency: именно генератор, НЕ @contextmanager
def get_session() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
