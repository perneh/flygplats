from sqlalchemy import Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Hole(Base):
    __tablename__ = "holes"
    __table_args__ = (UniqueConstraint("course_id", "number", name="uq_hole_course_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    par: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    #: Hole length in metres (from init data); optional for legacy rows.
    length_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    tee_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    tee_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    green_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    green_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    tee_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tee_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    green_x: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    green_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    course: Mapped["Course"] = relationship(back_populates="holes")
    shots: Mapped[list["Shot"]] = relationship(back_populates="hole")
