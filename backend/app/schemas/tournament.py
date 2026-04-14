"""Tournament API schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TournamentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    play_date: date
    course_id: int = Field(..., gt=0)


class TournamentParticipantCreate(BaseModel):
    player_id: int = Field(..., gt=0)
    handicap: float = Field(..., ge=0, le=54)


class TournamentIdBody(BaseModel):
    tournament_id: int = Field(..., gt=0)


class TournamentParticipantAddBody(BaseModel):
    """POST /api/v1/tournaments/participants — IDs in JSON, not the path."""

    tournament_id: int = Field(..., gt=0)
    player_id: int = Field(..., gt=0)
    handicap: float = Field(..., ge=0, le=54)


class TournamentPlayerIdsBody(BaseModel):
    """POST /api/v1/tournaments/shot-detail."""

    tournament_id: int = Field(..., gt=0)
    player_id: int = Field(..., gt=0)


class ScorecardIdBody(BaseModel):
    """POST /api/v1/scorecards/detail."""

    scorecard_id: int = Field(..., gt=0)


class ScorecardHoleUpdateBody(BaseModel):
    """POST /api/v1/scorecards/hole — all identifiers in the body."""

    scorecard_id: int = Field(..., gt=0)
    hole_number: int = Field(..., ge=1, le=18)
    strokes: int = Field(..., ge=1, le=40)
    player_id: int = Field(..., gt=0)


class CourseBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TournamentParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    player_name: str
    handicap: float


class TournamentFlightRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sequence: int
    name: str
    player_ids: list[int]


class TournamentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    play_date: date
    course_id: int
    status: str
    created_at: datetime


class TournamentDetailRead(TournamentRead):
    course: CourseBrief
    participants: list[TournamentParticipantRead]
    flights: list[TournamentFlightRead]


class HoleScoreItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hole_number: int
    strokes: int | None


class ScorecardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tournament_id: int
    player_id: int
    player_name: str
    flight_id: int
    flight_sequence: int
    holes: list[HoleScoreItem]
    out_total: int
    in_total: int
    gross_total: int


class LeaderboardHoleRow(BaseModel):
    """One hole on the tournament scoreboard (gross vs par)."""

    hole_number: int
    par: int
    strokes: int | None
    to_par: int | None = Field(
        None,
        description="strokes − par for this hole when strokes are recorded (negative = under par).",
    )


class LeaderboardPlayerRow(BaseModel):
    """One player: rank, totals, and per-hole gross (tournament HoleScore)."""

    rank: int = Field(..., description="Competition rank (ties share the same rank; next rank skips).")
    player_id: int
    player_name: str
    gross_total: int = Field(..., description="Sum of recorded strokes (holes without a score count as 0).")
    to_par: int | None = Field(
        None,
        description="gross_total minus sum of par for holes where strokes were recorded.",
    )
    holes: list[LeaderboardHoleRow]


class TournamentLeaderboardRead(BaseModel):
    """Full leaderboard: positions, strokes per hole, vs par — from tournament scorecards + course par."""

    tournament_id: int
    tournament_name: str
    course_id: int
    course_name: str
    course_par_total: int = Field(..., description="Sum of par for holes 1–18 (missing hole defs default to par 4).")
    players: list[LeaderboardPlayerRow]


class TournamentShotDetailItem(BaseModel):
    """One tracked shot (Round/Shot) — distance is optional in the shots API."""

    shot_id: int
    order: int = Field(..., ge=1, description="Stroke index on this hole (1 = first shot).")
    distance_m: float | None = Field(None, description="Metres, from Shot.distance when present.")
    club: str
    x: float
    y: float


class TournamentHoleShotDetail(BaseModel):
    hole_number: int
    par: int
    stroke_count: int
    to_par: int = Field(..., description="stroke_count − par for this hole.")
    shots: list[TournamentShotDetailItem]


class TournamentPlayerShotDetailRead(BaseModel):
    """
    Per-shot breakdown when a **Round** exists for the same player, course, and **calendar day**
    as the tournament ``play_date``. Otherwise ``matched_round_id`` is null and ``holes`` is empty.
    Tournament HoleScore lines are separate from Round/Shots; this view is for tracked GPS shots only.
    """

    tournament_id: int
    player_id: int
    player_name: str
    matched_round_id: int | None
    match_note: str
    holes: list[TournamentHoleShotDetail]
