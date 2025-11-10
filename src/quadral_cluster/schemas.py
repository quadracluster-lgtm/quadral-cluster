from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from .models.domain import ApplicationStatusEnum


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

class UserCreate(BaseSchema):
    telegram_id: Optional[int] = None
    username: Optional[str] = Field(default=None, max_length=64)
    email: Optional[str] = Field(default=None, max_length=255)
    profile: ProfileCreate


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
