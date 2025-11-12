from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

from quadral_cluster.domain.socionics import QUADRA_MEMBERS, Quadra, SocType
from quadral_cluster.models.domain import Cluster, ClusterMembership, Profile

SOCIONICS_TO_QUADRA = {
    soc_type.value: quadra.value.capitalize()
    for quadra, members in QUADRA_MEMBERS.items()
    for soc_type in members
}


@dataclass
class CompatibilityBreakdown:
    socionics: float
    psycho: float
    age: float
    geo: float
    activity: float
    reputation: float

    @property
    def total(self) -> float:
        return (
            50 * self.socionics
            + 20 * self.psycho
            + 10 * self.age
            + 8 * self.geo
            + 6 * self.activity
            + 6 * self.reputation
        )


def _quadra_for_profile(profile: Optional[Profile]) -> Optional[str]:
    if profile is None or profile.socionics_type is None:
        return None
    return SOCIONICS_TO_QUADRA.get(profile.socionics_type.upper())


def compute_breakdown(
    candidate: Profile,
    cluster: Cluster,
    member_profiles: Iterable[Profile],
) -> CompatibilityBreakdown:
    """Calculate a compatibility breakdown for the provided candidate and cluster."""

    socionics = _compute_socionics(candidate, cluster, member_profiles)
    psycho = _compute_psycho(candidate, cluster)
    age = _compute_age(candidate, member_profiles)
    geo = _compute_geo(candidate, cluster)
    activity = max(0.0, min(1.0, cluster.activity_score))
    reputation = max(0.0, min(1.0, candidate.reputation_score))

    return CompatibilityBreakdown(
        socionics=socionics,
        psycho=psycho,
        age=age,
        geo=geo,
        activity=activity,
        reputation=reputation,
    )


def _compute_socionics(candidate: Profile, cluster: Cluster, member_profiles: Iterable[Profile]) -> float:
    candidate_quadra = _quadra_for_profile(candidate)
    if candidate_quadra is None:
        return 0.0

    if cluster.target_quadra:
        return 1.0 if candidate_quadra.lower() == cluster.target_quadra.lower() else 0.0

    member_quadras = {
        quadra
        for profile in member_profiles
        if (quadra := _quadra_for_profile(profile)) is not None
    }
    if not member_quadras:
        return 0.5
    return 1.0 if candidate_quadra in member_quadras else 0.0


def _compute_psycho(candidate: Profile, cluster: Cluster) -> float:
    if candidate.psychotype is None:
        return 0.0
    if cluster.target_psychotype is None:
        return 0.5
    return 1.0 if candidate.psychotype.lower() == cluster.target_psychotype.lower() else 0.0


def _compute_age(candidate: Profile, member_profiles: Iterable[Profile]) -> float:
    if candidate.age is None:
        return 0.0
    ages = [profile.age for profile in member_profiles if profile.age is not None]
    if not ages:
        return 0.5
    avg_age = sum(ages) / len(ages)
    diff = abs(candidate.age - avg_age)
    if diff <= 5:
        return 1.0
    if diff <= 10:
        return 0.5
    return 0.0


def _compute_geo(candidate: Profile, cluster: Cluster) -> float:
    if candidate.city and cluster.city and candidate.city.lower() == cluster.city.lower():
        return 1.0
    if candidate.timezone and cluster.timezone and candidate.timezone == cluster.timezone:
        return 0.5
    return 0.0


def evaluate_candidate(
    candidate: Profile, cluster: Cluster, memberships: Iterable[ClusterMembership]
) -> Tuple[float, CompatibilityBreakdown]:
    """Return both the compatibility score and detailed breakdown."""

    member_profiles = [membership.user.profile for membership in memberships if membership.user.profile]
    breakdown = compute_breakdown(candidate, cluster, member_profiles)
    return round(breakdown.total, 2), breakdown


def score_candidate_for_cluster(
    candidate: Profile, cluster: Cluster, memberships: Iterable[ClusterMembership]
) -> float:
    score, _ = evaluate_candidate(candidate, cluster, memberships)
    return score


def _extract_field(entity: object, field: str) -> Optional[object]:
    if isinstance(entity, dict):
        return entity.get(field)
    return getattr(entity, field, None)


def _coerce_soc_type(value: object) -> Optional[SocType]:
    if isinstance(value, SocType):
        return value
    if value is None:
        return None
    text = str(value)
    if text.startswith("SocType."):
        text = text.split(".", 1)[1]
    text = text.upper()
    try:
        return SocType(text)
    except ValueError:
        return None


def build_quadra_cluster(users: list, target_quadra: Quadra) -> dict:
    """Select one representative per sociotype for the requested quadra."""

    required_types = {soc_type: None for soc_type in QUADRA_MEMBERS[target_quadra]}

    for user in users:
        soc_type = _coerce_soc_type(_extract_field(user, "socionics_type"))
        if soc_type is None:
            continue
        if soc_type not in required_types or required_types[soc_type] is not None:
            continue

        user_id = _extract_field(user, "id")
        if user_id is None:
            continue
        required_types[soc_type] = user_id

    missing = [soc_type.value for soc_type, member_id in required_types.items() if member_id is None]
    if missing:
        return {"ok": False, "missing": missing}

    members = [member_id for member_id in required_types.values() if member_id is not None]
    return {"ok": True, "members": members}
