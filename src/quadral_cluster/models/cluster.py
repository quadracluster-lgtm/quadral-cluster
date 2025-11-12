from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quadral_cluster.database import Base


if TYPE_CHECKING:
    from .user import User


class MatchingCluster(Base):
    __tablename__ = "matching_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quadra: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="locked")
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


class MatchingClusterMember(Base):
    __tablename__ = "matching_cluster_members"
    __table_args__ = (
        UniqueConstraint("cluster_id", "socionics_type", name="uq_cluster_tim"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("matching_clusters.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    socionics_type: Mapped[str] = mapped_column(String(8), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    cluster: Mapped[MatchingCluster] = relationship(
        "quadral_cluster.models.cluster.MatchingCluster",
        back_populates="members",
    )
    user: Mapped["User"] = relationship("User", back_populates="matching_membership")


Cluster = MatchingCluster
ClusterMember = MatchingClusterMember


__all__ = ["Cluster", "ClusterMember", "MatchingCluster", "MatchingClusterMember"]
