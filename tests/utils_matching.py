from __future__ import annotations

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from quadral_cluster.database import Base
from quadral_cluster.domain.socionics import Quadra, SocType
from quadral_cluster.models import availability, cluster, domain, preference  # noqa: F401
from quadral_cluster.models.domain import User


def create_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory()


def make_user(session: Session, tim: SocType, quadra: Quadra) -> User:
    user = User(
        username=f"user_{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        socionics_type=tim.value,
        quadra=quadra.value,
    )
    session.add(user)
    session.flush()
    return user
