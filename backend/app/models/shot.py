from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Shot(Base):
    __tablename__ = "shots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("rounds.id", ondelete="CASCADE"), index=True)
    hole_id: Mapped[int] = mapped_column(ForeignKey("holes.id", ondelete="CASCADE"), index=True)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    club: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    shot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    round: Mapped["Round"] = relationship(back_populates="shots")
    hole: Mapped["Hole"] = relationship(back_populates="shots")
