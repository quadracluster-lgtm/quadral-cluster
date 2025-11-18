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


@pytest.fixture()
def db_session() -> Session:
    session = create_session()
    try:
        yield session
    finally:
        session.close()


def test_path_a_join_and_conflict(db_session: Session) -> None:
    quadra = Quadra.ALPHA
    owner = make_user(db_session, SocType.ILE, quadra)
    first_candidate = make_user(db_session, SocType.SEI, quadra)
    second_candidate = make_user(db_session, SocType.SEI, quadra)

    cluster = Cluster(quadra=quadra.value, status="assembling", cluster_type=ClusterTypeEnum.FAMILY.value)
    db_session.add(cluster)
    db_session.flush()
    db_session.add(
        ClusterMember(
            cluster_id=cluster.id,
            user_id=owner.id,
            socionics_type=SocType.ILE.value,
        )
    )
    db_session.flush()

    open_clusters = list_open_clusters_for_tim(
        quadra, SocType.SEI, ClusterTypeEnum.FAMILY, session=db_session
    )
    assert open_clusters and open_clusters[0].cluster.id == cluster.id

    result_ok = try_join_cluster(
        first_candidate.id, cluster.id, intent_type=ClusterTypeEnum.FAMILY, session=db_session
    )
    assert result_ok == {"ok": True}

    conflict = try_join_cluster(
        second_candidate.id, cluster.id, intent_type=ClusterTypeEnum.FAMILY, session=db_session
    )
    assert conflict == {"ok": False, "reason": "slot_taken"}


def test_path_b_find_or_create_full_cluster(db_session: Session) -> None:
    quadra = Quadra.GAMMA
    users = {
        tim: make_user(db_session, tim, quadra)
        for tim in sorted(QUADRA_MEMBERS[quadra], key=lambda t: t.value)
    }

    initiator = next(iter(users.values()))
    result = find_or_create_cluster_for_user(
        initiator.id, quadra, cluster_type=ClusterTypeEnum.FAMILY, session=db_session
    )

    assert result["ok"] is True
    assert len(result["members"]) == 4

    cluster = db_session.get(Cluster, result["cluster_id"])
    assert cluster is not None
    assert cluster.status == "ready"


def test_path_b_missing_members(db_session: Session) -> None:
    quadra = Quadra.DELTA
    initiator = make_user(db_session, SocType.IEE, quadra)

    result = find_or_create_cluster_for_user(
        initiator.id, quadra, cluster_type=ClusterTypeEnum.FAMILY, session=db_session
    )
    assert result["ok"] is False
    missing = set(result["missing"])
    expected_missing = {tim.value for tim in QUADRA_MEMBERS[quadra] if tim != SocType.IEE}
    assert expected_missing <= missing
