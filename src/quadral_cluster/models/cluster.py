from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quadral_cluster.database import Base


if TYPE_CHECKING:
    from .user import User


class ClusterTypeEnum(str, Enum):
    FAMILY = "family"
    WORK = "work"


class MatchRequestStatus(str, Enum):
    PENDING = "pending"
    MATCHED = "matched"
    CANCELLED = "cancelled"


class MatchingCluster(Base):
    __tablename__ = "matching_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quadra: Mapped[str] = mapped_column(String(16), nullable=False)
    cluster_type: Mapped[str] = mapped_column(String(16), nullable=False, default=ClusterTypeEnum.FAMILY.value)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="assembling")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    members: Mapped[list["MatchingClusterMember"]] = relationship(
        "quadral_cluster.models.cluster.MatchingClusterMember",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )
    match_requests: Mapped[list["MatchRequest"]] = relationship(
        "quadral_cluster.models.cluster.MatchRequest",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )
    chat_rooms: Mapped[list["ChatRoom"]] = relationship(
        "quadral_cluster.models.cluster.ChatRoom",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )


class MatchingClusterMember(Base):
    __tablename__ = "matching_cluster_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("matching_clusters.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    match_request_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("match_requests.id", ondelete="SET NULL"), nullable=True
    )
    socionics_type: Mapped[str] = mapped_column(String(8), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    cluster: Mapped[MatchingCluster] = relationship(
        "quadral_cluster.models.cluster.MatchingCluster",
        back_populates="members",
    )
    user: Mapped["User"] = relationship("User", back_populates="matching_memberships")
    match_request: Mapped[MatchRequest | None] = relationship(
        "quadral_cluster.models.cluster.MatchRequest", back_populates="members"
    )


class MatchRequest(Base):
    __tablename__ = "match_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    quadra: Mapped[str] = mapped_column(String(16), nullable=False)
    socionics_type: Mapped[str] = mapped_column(String(8), nullable=False)
    intent_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ClusterTypeEnum.FAMILY.value
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=MatchRequestStatus.PENDING.value)
    cluster_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("matching_clusters.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="match_requests")
    cluster: Mapped[MatchingCluster | None] = relationship(
        "quadral_cluster.models.cluster.MatchingCluster",
        back_populates="match_requests",
    )
    members: Mapped[list[MatchingClusterMember]] = relationship(
        "quadral_cluster.models.cluster.MatchingClusterMember",
        back_populates="match_request",
    )


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("matching_clusters.id", ondelete="SET NULL"), nullable=True
    )
    topic: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    cluster: Mapped[MatchingCluster | None] = relationship(
        "quadral_cluster.models.cluster.MatchingCluster",
        back_populates="chat_rooms",
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "quadral_cluster.models.cluster.ChatMessage",
        back_populates="room",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    room: Mapped[ChatRoom] = relationship(
        "quadral_cluster.models.cluster.ChatRoom", back_populates="messages"
    )
    sender: Mapped[User | None] = relationship("User")


Cluster = MatchingCluster
ClusterMember = MatchingClusterMember


__all__ = [
    "Cluster",
    "ClusterMember",
    "MatchingCluster",
    "MatchingClusterMember",
    "MatchRequest",
    "ChatRoom",
    "ChatMessage",
    "ClusterTypeEnum",
    "MatchRequestStatus",
]
