from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from quadral_cluster.domain.socionics import QUADRA_MEMBERS, Quadra, SocType
from quadral_cluster.models.cluster import Cluster, ClusterMember, ClusterTypeEnum
from quadral_cluster.services.matching import (
    find_or_create_cluster_for_user,
    list_open_clusters_for_tim,
    try_join_cluster,
)

from .utils_matching import create_session, make_user


def setup_function() -> None:  # pragma: no cover - compatibility hook
    """Reset state before tests if needed."""


def teardown_function() -> None:  # pragma: no cover - compatibility hook
    """Reset state after tests if needed."""


def test_work_cluster_allows_expansion(db_session: Session) -> None:
    quadra = Quadra.BETA
    users = {tim: make_user(db_session, tim, quadra) for tim in QUADRA_MEMBERS[quadra]}
    initiator = next(iter(users.values()))

    result = find_or_create_cluster_for_user(
        initiator.id, quadra, cluster_type=ClusterTypeEnum.WORK, session=db_session
    )

    assert result["ok"] is True
    cluster_id = result["cluster_id"]
    cluster = db_session.get(Cluster, cluster_id)
    assert cluster is not None
    assert cluster.cluster_type == ClusterTypeEnum.WORK.value
    assert cluster.status == "ready"

    extra_tim = next(iter(QUADRA_MEMBERS[quadra]))
    extra_member = make_user(db_session, extra_tim, quadra)
    join_result = try_join_cluster(
        extra_member.id, cluster_id, intent_type=ClusterTypeEnum.WORK, session=db_session
    )
    assert join_result == {"ok": True}

    db_session.refresh(cluster)
    assert len(cluster.members) == 5
    assert cluster.status == "ready"


def test_intents_are_isolated(db_session: Session) -> None:
    quadra = Quadra.ALPHA
    owner = make_user(db_session, SocType.ILE, quadra)
    candidate = make_user(db_session, SocType.SEI, quadra)

    cluster = Cluster(
        quadra=quadra.value,
        cluster_type=ClusterTypeEnum.FAMILY.value,
        status="assembling",
    )
    db_session.add(cluster)
    db_session.flush()
    db_session.add(
        ClusterMember(
            cluster_id=cluster.id,
            user_id=owner.id,
            socionics_type=owner.socionics_type,
        )
    )
    db_session.flush()

    open_for_work = list_open_clusters_for_tim(
        quadra, SocType.SEI, ClusterTypeEnum.WORK, session=db_session
    )
    assert open_for_work == []

    result = try_join_cluster(
        candidate.id, cluster.id, intent_type=ClusterTypeEnum.WORK, session=db_session
    )
    assert result == {"ok": False, "reason": "intent_mismatch"}


def test_family_cluster_completes_four(db_session: Session) -> None:
    quadra = Quadra.DELTA
    users = {tim: make_user(db_session, tim, quadra) for tim in QUADRA_MEMBERS[quadra]}
    initiator = next(iter(users.values()))

    result = find_or_create_cluster_for_user(
        initiator.id, quadra, cluster_type=ClusterTypeEnum.FAMILY, session=db_session
    )

    assert result["ok"] is True
    assert len(result["members"]) == 4
    cluster = db_session.get(Cluster, result["cluster_id"])
    assert cluster is not None
    assert cluster.cluster_type == ClusterTypeEnum.FAMILY.value
    assert cluster.status == "ready"


# Fixtures


@pytest.fixture()
def db_session() -> Session:
    session = create_session()
    try:
        yield session
    finally:
        session.close()
