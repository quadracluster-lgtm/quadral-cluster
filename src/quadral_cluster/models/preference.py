from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quadral_cluster.database import Base


class Preference(Base):
    __tablename__ = "preferences"

    from_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    to_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    from_user: Mapped["User"] = relationship(
        back_populates="preferences_from", foreign_keys=[from_user_id]
    )
    to_user: Mapped["User"] = relationship(
        back_populates="preferences_to", foreign_keys=[to_user_id]
    )


__all__ = ["Preference"]
