from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from quadral_cluster.database import SessionLocal
from quadral_cluster.domain.socionics import QUADRA_MEMBERS, Quadra, SocType
from quadral_cluster.models.cluster import (
    Cluster,
    ClusterMember,
    ClusterTypeEnum,
    MatchRequest,
    MatchRequestStatus,
)
from quadral_cluster.models.domain import User
from quadral_cluster.models.preference import Preference
from quadral_cluster.utils.time_overlap import overlap as availability_overlap


class MatchingError(Exception):
    """Base class for matching service errors."""


@dataclass(slots=True)
class ClusterWithScore:
    cluster: Cluster
    score: float
    members: Sequence[ClusterMember]


def _ensure_session(session: Session | None) -> tuple[Session, bool]:
    if session is not None:
        return session, False
    new_session = SessionLocal()
    return new_session, True


def _close_session(session: Session, should_close: bool) -> None:
    if should_close:
        session.close()


def _ensure_user_belongs_to_quadra(user: User, quadra: Quadra) -> None:
    members = QUADRA_MEMBERS[quadra]
    if SocType(user.socionics_type) not in members:
        msg = f"User {user.id} with TIM {user.socionics_type} is not part of quadra {quadra.value}"
        raise MatchingError(msg)


def _create_match_request(
    *,
    session: Session,
    user: User,
    quadra: Quadra,
    intent_type: ClusterTypeEnum,
    status: MatchRequestStatus = MatchRequestStatus.PENDING,
    cluster: Cluster | None = None,
) -> MatchRequest:
    request = MatchRequest(
        user_id=user.id,
        quadra=quadra.value,
        socionics_type=user.socionics_type,
        intent_type=intent_type.value,
        status=status.value,
        cluster=cluster,
    )
    session.add(request)
    session.flush()
    return request


def _update_cluster_status(cluster: Cluster, cluster_type: ClusterTypeEnum) -> None:
    quadra = Quadra(cluster.quadra)
    required = set(QUADRA_MEMBERS[quadra])
    member_tims = {SocType(member.socionics_type) for member in cluster.members}

    if cluster_type == ClusterTypeEnum.FAMILY:
        if member_tims >= required and len(cluster.members) == len(required):
            cluster.status = "ready"
        else:
            cluster.status = "assembling"
    else:
        cluster.status = "ready" if required.issubset(member_tims) else "assembling"


def _load_preference_map(preferences: Iterable[Preference]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for pref in preferences:
        mapping[pref.to_user_id] = max(min(pref.weight, 2), -2)
    return mapping


def _timezone_score(a: User, b: User) -> float:
    if not a.timezone or not b.timezone:
        return 0.5
    try:
        from zoneinfo import ZoneInfo
    except Exception:  # pragma: no cover - optional dependency fallback
        return 0.5

    try:
        now = datetime.utcnow()
        delta_a = now.astimezone(ZoneInfo(a.timezone)).utcoffset()
        delta_b = now.astimezone(ZoneInfo(b.timezone)).utcoffset()
    except Exception:  # pragma: no cover - invalid timezone name
        return 0.0

    if delta_a is None or delta_b is None:
        return 0.5

    diff_hours = abs((delta_a - delta_b).total_seconds()) / 3600.0
    return max(0.0, 1.0 - min(diff_hours, 12.0) / 12.0)


def _age_score(a: User, b: User) -> float:
    if a.age is None or b.age is None:
        return 0.5
    diff = abs(a.age - b.age)
    if diff >= 20:
        return 0.0
    return max(0.0, 1.0 - diff / 20.0)


def pair_score(a: User, b: User) -> float:
    """Calculate compatibility score between two users."""

    prefs_from_a = _load_preference_map(a.preferences_from)
    prefs_from_b = _load_preference_map(b.preferences_from)

    like_a = (prefs_from_a.get(b.id, 0) + 2) / 4
    like_b = (prefs_from_b.get(a.id, 0) + 2) / 4
    like_score = (like_a + like_b) / 2

    mask_a = a.availability.weekly_mask if a.availability else ""
    mask_b = b.availability.weekly_mask if b.availability else ""
    time_score = availability_overlap(mask_a, mask_b)

    zone_score = _timezone_score(a, b)
    age_score = _age_score(a, b)

    return (like_score * 0.5) + (time_score * 0.3) + (zone_score * 0.1) + (age_score * 0.1)


def _can_join_cluster(cluster: Cluster, tim: SocType, cluster_type: ClusterTypeEnum) -> bool:
    if cluster.cluster_type != cluster_type.value:
        return False
    if cluster.status == "archived":
        return False

    cluster_quadra = Quadra(cluster.quadra)
    if tim not in QUADRA_MEMBERS[cluster_quadra]:
        return False

    members = list(cluster.members)
    tims_in_cluster = {SocType(member.socionics_type) for member in members}

    if cluster_type == ClusterTypeEnum.FAMILY:
        if tim in tims_in_cluster:
            return False
        if len(members) >= len(QUADRA_MEMBERS[cluster_quadra]):
            return False
        return True

    return True


def list_open_clusters_for_tim(
    quadra: Quadra,
    tim: SocType,
    cluster_type: ClusterTypeEnum,
    limit: int = 10,
    *,
    session: Session | None = None,
    candidate: User | None = None,
) -> list[ClusterWithScore]:
    db, should_close = _ensure_session(session)
    try:
        stmt = (
            select(Cluster)
            .where(Cluster.quadra == quadra.value)
            .where(Cluster.cluster_type == cluster_type.value)
            .where(Cluster.status.in_(["assembling", "ready"]))
            .options(joinedload(Cluster.members).joinedload(ClusterMember.user))
            .limit(limit)
        )
        clusters = db.execute(stmt).scalars().unique().all()

        result: list[ClusterWithScore] = []
        for cluster in clusters:
            members = [member for member in cluster.members]
            if not _can_join_cluster(cluster, tim, cluster_type):
                continue

            score = 0.0
            if candidate is not None:
                score_values = [pair_score(candidate, member.user) for member in members]
                score = sum(score_values) / len(score_values) if score_values else 0.5
            else:
                score = len(members) / max(len(QUADRA_MEMBERS[quadra]), 1)

            result.append(ClusterWithScore(cluster=cluster, score=score, members=members))

        result.sort(key=lambda item: item.score, reverse=True)
        return result[:limit]
    finally:
        _close_session(db, should_close)


def _ensure_can_join(cluster: Cluster, user: User, tim: SocType) -> None:
    allowed_tims = QUADRA_MEMBERS[Quadra(cluster.quadra)]
    if tim not in allowed_tims:
        msg = f"TIM {tim.value} is not part of cluster quadra {cluster.quadra}"
        raise MatchingError(msg)

    existing_tims = {SocType(member.socionics_type) for member in cluster.members}
    if cluster.cluster_type == ClusterTypeEnum.FAMILY.value and tim in existing_tims:
        raise MatchingError("slot_taken")

    if cluster.status == "archived":
        raise MatchingError("archived")

    if cluster.cluster_type == ClusterTypeEnum.FAMILY.value and len(cluster.members) >= len(allowed_tims):
        raise MatchingError("slot_taken")


def try_join_cluster(
    user_id: int,
    cluster_id: int,
    *,
    intent_type: ClusterTypeEnum | None = None,
    session: Session | None = None,
) -> dict[str, object]:
    db, should_close = _ensure_session(session)
    try:
        user = db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                joinedload(User.availability),
                joinedload(User.preferences_from),
                joinedload(User.preferences_to),
                joinedload(User.match_requests),
                joinedload(User.matching_memberships).joinedload(ClusterMember.cluster),
            )
        ).unique().scalar_one_or_none()
        if user is None:
            raise MatchingError(f"User {user_id} not found")

        cluster = db.execute(
            select(Cluster)
            .where(Cluster.id == cluster_id)
            .options(joinedload(Cluster.members).joinedload(ClusterMember.user))
        ).unique().scalar_one_or_none()
        if cluster is None:
            raise MatchingError(f"Cluster {cluster_id} not found")

        cluster_type = intent_type or ClusterTypeEnum(cluster.cluster_type)
        if cluster.cluster_type != cluster_type.value:
            raise MatchingError("intent_mismatch")
        tim = SocType(user.socionics_type)
        _ensure_can_join(cluster, user, tim)
        _ensure_user_belongs_to_quadra(user, Quadra(cluster.quadra))

        request = _create_match_request(
            session=db,
            user=user,
            quadra=Quadra(cluster.quadra),
            intent_type=cluster_type,
            status=MatchRequestStatus.MATCHED,
            cluster=cluster,
        )

        membership = ClusterMember(
            cluster_id=cluster.id,
            user_id=user.id,
            socionics_type=tim.value,
            match_request_id=request.id,
        )
        cluster.members.append(membership)

        _update_cluster_status(cluster, cluster_type)

        db.flush()
        return {"ok": True}
    except MatchingError as exc:
        reason = str(exc) or "matching_error"
        return {"ok": False, "reason": reason}
    finally:
        _close_session(db, should_close)


def _best_candidates_for_tim(
    db: Session,
    quadra: Quadra,
    tim: SocType,
    exclude: set[int],
    anchor: User,
    cluster_type: ClusterTypeEnum,
) -> list[User]:
    stmt = (
        select(User)
        .where(User.socionics_type == tim.value)
        .where(User.id.notin_(exclude))
        .options(
            joinedload(User.availability),
            joinedload(User.preferences_from),
            joinedload(User.preferences_to),
        )
    )
    users = []
    for user in db.execute(stmt).unique().scalars():
        if user.quadra != quadra.value:
            continue
        active_memberships = [
            membership
            for membership in user.matching_memberships
            if membership.cluster and membership.cluster.cluster_type == cluster_type.value
        ]
        if active_memberships:
            continue
        users.append(user)

    scored = [(pair_score(anchor, candidate), candidate) for candidate in users]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [candidate for _, candidate in scored]


def find_or_create_cluster_for_user(
    user_id: int,
    quadra: Quadra,
    *,
    cluster_type: ClusterTypeEnum,
    session: Session | None = None,
) -> dict[str, object]:
    db, should_close = _ensure_session(session)
    try:
        user = db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                joinedload(User.availability),
                joinedload(User.preferences_from),
                joinedload(User.preferences_to),
                joinedload(User.match_requests),
                joinedload(User.matching_memberships).joinedload(ClusterMember.cluster),
            )
        ).unique().scalar_one_or_none()
        if user is None:
            raise MatchingError(f"User {user_id} not found")

        _ensure_user_belongs_to_quadra(user, quadra)

        existing_membership = next(
            (
                membership
                for membership in user.matching_memberships
                if membership.cluster and membership.cluster.cluster_type == cluster_type.value
            ),
            None,
        )
        if existing_membership and existing_membership.cluster:
            cluster = existing_membership.cluster
            members = [member for member in cluster.members]
            return {
                "ok": True,
                "cluster_id": cluster.id,
                "members": [
                    {"user_id": member.user_id, "socionics_type": member.socionics_type}
                    for member in members
                ],
            }

        request = _create_match_request(
            session=db,
            user=user,
            quadra=quadra,
            intent_type=cluster_type,
            status=MatchRequestStatus.PENDING,
        )

        required = QUADRA_MEMBERS[quadra]
        missing: list[str] = []

        selected: dict[SocType, User] = {SocType(user.socionics_type): user}
        exclude_ids = {user.id}

        for tim in required:
            if tim == SocType(user.socionics_type):
                continue
            candidates = _best_candidates_for_tim(
                db, quadra, tim, exclude_ids, user, cluster_type
            )
            if not candidates:
                missing.append(tim.value)
                continue
            selected[tim] = candidates[0]
            exclude_ids.add(candidates[0].id)

        if missing:
            return {"ok": False, "missing": missing}

        cluster = Cluster(
            quadra=quadra.value,
            status="assembling",
            cluster_type=cluster_type.value,
        )
        db.add(cluster)
        db.flush()

        members_payload = []
        for tim, member_user in selected.items():
            membership = ClusterMember(
                cluster_id=cluster.id,
                user_id=member_user.id,
                socionics_type=tim.value,
                match_request_id=request.id if member_user.id == user.id else None,
            )
            cluster.members.append(membership)
            members_payload.append({"user_id": member_user.id, "socionics_type": tim.value})

        _update_cluster_status(cluster, cluster_type)
        request.status = MatchRequestStatus.MATCHED.value
        request.cluster_id = cluster.id

        db.flush()
        return {"ok": True, "cluster_id": cluster.id, "members": members_payload}
    finally:
        _close_session(db, should_close)
