from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quadral_cluster.database import Base

if TYPE_CHECKING:
    from .availability import Availability
    from .cluster import MatchingClusterMember, MatchRequest
    from .preference import Preference


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    socionics_type: Mapped[str] = mapped_column(String(8), nullable=False)
    quadra: Mapped[Optional[str]] = mapped_column(String(16))
    timezone: Mapped[Optional[str]] = mapped_column(String(64))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    city: Mapped[Optional[str]] = mapped_column(String(120))

    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    memberships: Mapped[List["ClusterMembership"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    applications: Mapped[List["Application"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    test_results: Mapped[List["TestResult"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    availability: Mapped[Optional["Availability"]] = relationship(
        "Availability", back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    preferences_from: Mapped[List["Preference"]] = relationship(
        "Preference",
        back_populates="from_user",
        cascade="all, delete-orphan",
        foreign_keys="Preference.from_user_id",
    )
    preferences_to: Mapped[List["Preference"]] = relationship(
        "Preference",
        back_populates="to_user",
        cascade="all, delete-orphan",
        foreign_keys="Preference.to_user_id",
    )
    matching_memberships: Mapped[List["MatchingClusterMember"]] = relationship(
        "MatchingClusterMember", back_populates="user", cascade="all, delete-orphan"
    )
    match_requests: Mapped[List["MatchRequest"]] = relationship(
        "MatchRequest", back_populates="user", cascade="all, delete-orphan"
    )


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    age: Mapped[Optional[int]] = mapped_column(Integer)
    bio: Mapped[Optional[str]] = mapped_column(String(300))
    city: Mapped[Optional[str]] = mapped_column(String(120))
    timezone: Mapped[Optional[str]] = mapped_column(String(64))
    interests: Mapped[Optional[List[str]]] = mapped_column(JSON)
    socionics_type: Mapped[Optional[str]] = mapped_column(String(8))
    psychotype: Mapped[Optional[str]] = mapped_column(String(32))
    reputation_score: Mapped[float] = mapped_column(Float, default=0.5)
    activity_score: Mapped[float] = mapped_column(Float, default=0.5)

    user: Mapped[User] = relationship(back_populates="profile")


class Cluster(Base, TimestampMixin):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    language: Mapped[str] = mapped_column(String(32), default="ru")
    city: Mapped[Optional[str]] = mapped_column(String(120))
    timezone: Mapped[Optional[str]] = mapped_column(String(64))
    target_quadra: Mapped[Optional[str]] = mapped_column(String(16))
    target_psychotype: Mapped[Optional[str]] = mapped_column(String(32))
    activity_score: Mapped[float] = mapped_column(Float, default=0.5)
    reputation_score: Mapped[float] = mapped_column(Float, default=0.5)

    memberships: Mapped[List["ClusterMembership"]] = relationship(
        back_populates="cluster", cascade="all, delete-orphan"
    )
    applications: Mapped[List["Application"]] = relationship(
        back_populates="cluster", cascade="all, delete-orphan"
    )


class ClusterMembership(Base, TimestampMixin):
    __tablename__ = "cluster_memberships"
    __table_args__ = (UniqueConstraint("user_id", "cluster_id", name="uq_user_cluster"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(32), default="member")

    cluster: Mapped[Cluster] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class ApplicationStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id", ondelete="CASCADE"))
    status: Mapped[ApplicationStatusEnum] = mapped_column(
        SQLEnum(ApplicationStatusEnum, native_enum=False),
        default=ApplicationStatusEnum.PENDING,
        nullable=False,
    )
    compatibility_score: Mapped[Optional[float]] = mapped_column(Float)

    user: Mapped[User] = relationship(back_populates="applications")
    cluster: Mapped[Cluster] = relationship(back_populates="applications")


class TestResult(Base, TimestampMixin):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    test_type: Mapped[str] = mapped_column(String(32))
    socionics_type: Mapped[Optional[str]] = mapped_column(String(8))
    psychotype: Mapped[Optional[str]] = mapped_column(String(32))
    confidence: Mapped[Optional[float]] = mapped_column(Float)

    user: Mapped[User] = relationship(back_populates="test_results")
