from sqlalchemy import Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GolfClub(Base):
    __tablename__ = "golf_clubs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    catalog_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    club_type: Mapped[str] = mapped_column(String(64), nullable=False)
    loft_deg: Mapped[float] = mapped_column(Float, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)
    max_distance_m: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_distance_m: Mapped[int] = mapped_column(Integer, nullable=False)
    player_levels: Mapped[list[str]] = mapped_column(JSON, nullable=False)
