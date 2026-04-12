from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.round import RoundRead


class MatchShotIn(BaseModel):
    """Single stroke on canvas / measurement (same fields as ``ShotCreate`` without ids)."""

    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    club: str = Field("", max_length=64)
    distance: float | None = None


class MatchPlayerHoleIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_id: int = Field(..., ge=1)
    shots: list[MatchShotIn] = Field(default_factory=list)


class MatchHoleIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hole_number: int = Field(..., ge=1, le=18)
    by_player: list[MatchPlayerHoleIn] = Field(default_factory=list)


class MatchCreate(BaseModel):
    """Start one round per player on ``course_id``, then record shots per hole."""

    model_config = ConfigDict(extra="forbid")

    course_id: int = Field(..., ge=1)
    player_ids: list[int] = Field(..., min_length=1)
    holes: list[MatchHoleIn] = Field(default_factory=list)
    #: If set, all rounds in this match get this finish time (e.g. end of round).
    finished_at: datetime | None = None

    @field_validator("player_ids")
    @classmethod
    def unique_players(cls, v: list[int]) -> list[int]:
        seen: set[int] = set()
        out: list[int] = []
        for pid in v:
            if pid in seen:
                continue
            seen.add(pid)
            out.append(pid)
        if not out:
            raise ValueError("player_ids must contain at least one distinct player")
        return out

    @field_validator("holes")
    @classmethod
    def unique_hole_numbers(cls, v: list[MatchHoleIn]) -> list[MatchHoleIn]:
        seen: set[int] = set()
        for h in v:
            if h.hole_number in seen:
                raise ValueError(f"duplicate hole_number {h.hole_number} in request")
            seen.add(h.hole_number)
        return v


class MatchRead(BaseModel):
    course_id: int
    rounds: list[RoundRead]
    shots_created: int
