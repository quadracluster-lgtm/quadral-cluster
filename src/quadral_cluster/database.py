from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from quadral_cluster.config import get_settings


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
def get_session() -> Iterator[Session]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
