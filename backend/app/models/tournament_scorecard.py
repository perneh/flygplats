"""Tournament scorecards: gross strokes per hole (1–18)."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Scorecard(Base):
    __tablename__ = "scorecards"
    __table_args__ = (UniqueConstraint("tournament_id", "player_id", name="uq_scorecard_tournament_player"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    flight_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tournament_flights.id", ondelete="CASCADE"), nullable=False, index=True
    )

    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="scorecards")
    player: Mapped["Player"] = relationship("Player", back_populates="scorecards")
    flight: Mapped["TournamentFlight"] = relationship("TournamentFlight", back_populates="scorecards")
    hole_scores: Mapped[list["HoleScore"]] = relationship(
        back_populates="scorecard",
        cascade="all, delete-orphan",
        order_by="HoleScore.hole_number",
    )


class HoleScore(Base):
    __tablename__ = "hole_scores"
    __table_args__ = (UniqueConstraint("scorecard_id", "hole_number", name="uq_hole_score_card_hole"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scorecard_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scorecards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hole_number: Mapped[int] = mapped_column(Integer, nullable=False)
    #: Null until a stroke count is recorded for this hole.
    strokes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    scorecard: Mapped["Scorecard"] = relationship("Scorecard", back_populates="hole_scores")
