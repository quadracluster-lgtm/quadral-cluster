from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from quadral_cluster.domain.socionics import Quadra, SocType
from quadral_cluster.models.cluster import Cluster, ClusterMember
from quadral_cluster.services.matching import try_join_cluster

from .utils_matching import create_session, make_user


@pytest.fixture()
def db_session() -> Session:
    session = create_session()
    try:
        yield session
    finally:
        session.close()


def test_cannot_add_same_tim_twice(db_session: Session) -> None:
    founder = make_user(db_session, SocType.ILE, Quadra.ALPHA)
    candidate = make_user(db_session, SocType.ILE, Quadra.ALPHA)

    cluster = Cluster(quadra=Quadra.ALPHA.value, status="locked")
    db_session.add(cluster)
    db_session.flush()
    db_session.add(
        ClusterMember(
            cluster_id=cluster.id,
            user_id=founder.id,
            socionics_type=SocType.ILE.value,
        )
    )
    db_session.flush()

    result = try_join_cluster(candidate.id, cluster.id, session=db_session)
    assert result == {"ok": False, "reason": "slot_taken"}


def test_cannot_join_foreign_quadra(db_session: Session) -> None:
    founder = make_user(db_session, SocType.ILE, Quadra.ALPHA)
    outsider = make_user(db_session, SocType.SEE, Quadra.GAMMA)

    cluster = Cluster(quadra=Quadra.ALPHA.value, status="locked")
    db_session.add(cluster)
    db_session.flush()
    db_session.add(
        ClusterMember(
            cluster_id=cluster.id,
            user_id=founder.id,
            socionics_type=SocType.ILE.value,
        )
    )
    db_session.flush()

    result = try_join_cluster(outsider.id, cluster.id, session=db_session)
    assert result["ok"] is False
    assert "quadra" in result["reason"].lower()
