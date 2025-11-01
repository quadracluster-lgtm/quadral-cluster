from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .models.domain import ApplicationStatusEnum


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ProfileCreate(BaseModel):
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


class UserCreate(BaseModel):
    telegram_id: Optional[int] = None
    username: Optional[str] = Field(default=None, max_length=64)
    email: Optional[str] = Field(default=None, max_length=255)
    profile: ProfileCreate


class UserRead(TimestampSchema):
    id: int
    telegram_id: Optional[int]
    username: Optional[str]
    email: Optional[str]
    profile: ProfileRead


class ClusterCreate(BaseModel):
    name: str
    language: str = Field(default="ru", max_length=32)
    city: Optional[str] = None
    timezone: Optional[str] = None
    target_quadra: Optional[str] = None
    target_psychotype: Optional[str] = None
    activity_score: float = Field(default=0.5, ge=0.0, le=1.0)
    reputation_score: float = Field(default=0.5, ge=0.0, le=1.0)
    founder_user_id: Optional[int] = Field(default=None, description="User that will become the cluster founder")


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


class Recommendation(BaseModel):
    cluster: ClusterRead
    compatibility_score: float = Field(ge=0.0, le=100.0)


class ApplicationCreate(BaseModel):
    user_id: int
    cluster_id: int


class ApplicationRead(TimestampSchema):
    id: int
    user_id: int
    cluster_id: int
    status: ApplicationStatusEnum
    compatibility_score: Optional[float]


class TestResultCreate(BaseModel):
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
