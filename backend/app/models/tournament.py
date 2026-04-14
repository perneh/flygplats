"""Golf tournaments: participants, flights, and links to courses."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TournamentStatus(StrEnum):
    DRAFT = "draft"
    STARTED = "started"
    FINISHED = "finished"


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    play_date: Mapped[date] = mapped_column(Date(), nullable=False)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=TournamentStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    course: Mapped["Course"] = relationship("Course", back_populates="tournaments")
    participants: Mapped[list["TournamentParticipant"]] = relationship(
        back_populates="tournament",
        cascade="all, delete-orphan",
        order_by="TournamentParticipant.id",
    )
    flights: Mapped[list["TournamentFlight"]] = relationship(
        back_populates="tournament",
        cascade="all, delete-orphan",
        order_by="TournamentFlight.sequence",
    )
    scorecards: Mapped[list["Scorecard"]] = relationship(
        "Scorecard",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"
    __table_args__ = (UniqueConstraint("tournament_id", "player_id", name="uq_tournament_player"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    #: World Handicap System style index (grouping only in MVP).
    handicap: Mapped[float] = mapped_column(Float, nullable=False)

    tournament: Mapped["Tournament"] = relationship(back_populates="participants")
    player: Mapped["Player"] = relationship("Player", back_populates="tournament_entries")


class TournamentFlight(Base):
    __tablename__ = "tournament_flights"
    __table_args__ = (UniqueConstraint("tournament_id", "sequence", name="uq_tournament_flight_seq"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    #: 1-based order within the tournament (Flight 1, Flight 2, …).
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    tournament: Mapped["Tournament"] = relationship(back_populates="flights")
    scorecards: Mapped[list["Scorecard"]] = relationship(
        "Scorecard", back_populates="flight"
    )
