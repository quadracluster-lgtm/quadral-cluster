from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

from ..models.domain import Cluster, ClusterMembership, Profile

SOCIONICS_TO_QUADRA = {
    "ILE": "Alpha",
    "SEI": "Alpha",
    "ESE": "Alpha",
    "LII": "Alpha",
    "SLE": "Beta",
    "IEI": "Beta",
    "EIE": "Beta",
    "LSI": "Beta",
    "LIE": "Gamma",
    "ESI": "Gamma",
    "SEE": "Gamma",
    "ILI": "Gamma",
    "LSE": "Delta",
    "EII": "Delta",
    "IEE": "Delta",
    "SLI": "Delta",
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
