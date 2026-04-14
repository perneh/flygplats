from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #: Optional stable id from ``golf_courses_25.json`` (not the DB PK).
    catalog_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    holes: Mapped[list["Hole"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Hole.number",
    )
    rounds: Mapped[list["Round"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )
    tournaments: Mapped[list["Tournament"]] = relationship(
        "Tournament",
        back_populates="course",
    )
