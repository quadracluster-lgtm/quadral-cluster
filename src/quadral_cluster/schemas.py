from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quadral_cluster.domain.socionics import QUADRA_MEMBERS, Quadra, SocType
from quadral_cluster.models.domain import ApplicationStatusEnum


class BaseSchema(BaseModel):
    """Common configuration for Pydantic schemas."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime


# ---------- Профиль пользователя ----------

class ProfileCreate(BaseSchema):
    age: Optional[int] = Field(default=None, ge=18, le=120)
    bio: Optional[str] = Field(default=None, max_length=300)
    city: Optional[str] = None
    timezone: Optional[str] = None
    interests: Optional[List[str]] = None
    socionics_type: Optional[str] = Field(default=None, max_length=8)
    psychotype: Optional[str] = Field(default=None, max_length=32)
    reputation_score: float = Field(default=0.5, ge=0.0, le=1.0)
    activity_score: float = Field(default=0.5, ge=0.0, le=1.0)


class ProfileRead(ProfileCreate, TimestampSchema):
    id: int


# ---------- Пользователь ----------

def _ensure_quadra(socionics_type: SocType, quadra: Quadra | None) -> Quadra | None:
    if quadra is not None:
        if socionics_type not in QUADRA_MEMBERS[quadra]:
            msg = (
                "Socionics type must belong to the specified quadra: "
                f"{socionics_type} ∉ {quadra.value}"
            )
            raise ValueError(msg)
        return quadra

    for candidate, members in QUADRA_MEMBERS.items():
        if socionics_type in members:
            return candidate
    return None


class UserCreate(BaseSchema):
    telegram_id: Optional[int] = None
    username: Optional[str] = Field(default=None, max_length=64)
    email: Optional[str] = Field(default=None, max_length=255)
    profile: ProfileCreate
    socionics_type: SocType
    quadra: Quadra | None = None

    @model_validator(mode="after")
    def _populate_quadra(self) -> "UserCreate":
        resolved = _ensure_quadra(self.socionics_type, self.quadra)
        object.__setattr__(self, "quadra", resolved)
        return self


class ProfileUpdate(BaseSchema):
    age: Optional[int] = Field(default=None, ge=18, le=120)
    bio: Optional[str] = Field(default=None, max_length=300)
    city: Optional[str] = None
    timezone: Optional[str] = None
    interests: Optional[List[str]] = None
    socionics_type: Optional[str] = Field(default=None, max_length=8)
    psychotype: Optional[str] = Field(default=None, max_length=32)
    reputation_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    activity_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class UserRead(TimestampSchema):
    id: int
    telegram_id: Optional[int]
    username: Optional[str]
    email: Optional[str]
    profile: Optional[ProfileRead]
    socionics_type: SocType
    quadra: Quadra | None = None

    @model_validator(mode="after")
    def _populate_quadra(self) -> "UserRead":
        resolved = _ensure_quadra(self.socionics_type, self.quadra)
        object.__setattr__(self, "quadra", resolved)
        return self


class UserPublic(BaseSchema):
    id: int
    username: Optional[str] = None
    socionics_type: SocType
    quadra: Quadra | None = None

    @model_validator(mode="after")
    def _populate_quadra(self) -> "UserPublic":
        resolved = _ensure_quadra(self.socionics_type, self.quadra)
        object.__setattr__(self, "quadra", resolved)
        return self


# ---------- Кластер ----------

class ClusterCreate(BaseSchema):
    name: str
    language: str = Field(default="ru", max_length=32)
    city: Optional[str] = None
    timezone: Optional[str] = None
    target_quadra: Optional[str] = None
    target_psychotype: Optional[str] = None
    activity_score: float = Field(default=0.5, ge=0.0, le=1.0)
    reputation_score: float = Field(default=0.5, ge=0.0, le=1.0)
    founder_user_id: Optional[int] = Field(
        default=None,
        description="User that will become the cluster founder",
    )


class ClusterRead(TimestampSchema):
    id: int
    name: str
    language: str
    city: Optional[str]
    timezone: Optional[str]
    target_quadra: Optional[str]
    target_psychotype: Optional[str]
    activity_score: float
    reputation_score: float


class ClusterMembershipRead(TimestampSchema):
    id: int
    cluster_id: int
    user_id: int
    role: str


# ---------- Матчмейкинг / Заявки ----------

class CompatibilityBreakdownRead(BaseSchema):
    socionics: float
    psycho: float
    age: float
    geo: float
    activity: float
    reputation: float


class Recommendation(BaseSchema):
    cluster: ClusterRead
    compatibility_score: float = Field(ge=0.0, le=100.0)
    breakdown: CompatibilityBreakdownRead


class ApplicationCreate(BaseSchema):
    user_id: int
    cluster_id: int


class ApplicationRead(TimestampSchema):
    id: int
    user_id: int
    cluster_id: int
    status: ApplicationStatusEnum
    compatibility_score: Optional[float]


# ---------- Тесты ----------

class TestResultCreate(BaseSchema):
    user_id: int
    test_type: str
    socionics_type: Optional[str] = None
    psychotype: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class TestResultRead(TimestampSchema):
    id: int
    user_id: int
    test_type: str
    socionics_type: Optional[str]
    psychotype: Optional[str]
    confidence: Optional[float]


class QuadraMatchRequest(BaseSchema):
    quadra: Quadra
    limit: int = Field(default=100, ge=4, le=500)


class QuadraMatchResponse(BaseSchema):
    quadra: Quadra
    ok: bool
    members: List[int] | None = None
    missing: List[str] | None = None


# ---------- Matching extensions ----------


class ClusterType(str, Enum):
    FAMILY = "family"
    WORK = "work"


class MatchRequestStatus(str, Enum):
    PENDING = "pending"
    MATCHED = "matched"
    CANCELLED = "cancelled"


class MatchRequestCreate(BaseSchema):
    user_id: int
    quadra: Quadra
    intent_type: ClusterType = ClusterType.FAMILY
    socionics_type: SocType


class MatchRequestRead(TimestampSchema):
    id: int
    user_id: int
    quadra: Quadra
    intent_type: ClusterType
    socionics_type: SocType
    status: MatchRequestStatus
    cluster_id: Optional[int] = None


class MatchingClusterMemberRead(BaseSchema):
    user_id: int
    socionics_type: SocType
    match_request_id: Optional[int] = None


class MatchingClusterRead(BaseSchema):
    id: int
    quadra: Quadra
    cluster_type: ClusterType
    status: str
    members: List[MatchingClusterMemberRead]
