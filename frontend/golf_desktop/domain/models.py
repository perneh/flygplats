from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RoundSummary:
    id: int
    player_id: int
    course_id: int
    started_at: datetime
    finished_at: datetime | None


@dataclass(frozen=True)
class HoleView:
    id: int
    course_id: int
    number: int
    par: int
    tee_x: float
    tee_y: float
    green_x: float
    green_y: float


@dataclass(frozen=True)
class ShotPoint:
    id: int
    round_id: int
    hole_id: int
    x: float
    y: float
    club: str
    distance: float | None
    shot_at: datetime
