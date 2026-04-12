from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.shot import ShotRead


class PerformanceHoleBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hole_number: int
    hole_id: int = Field(..., ge=1)
    par: int
    stroke_count: int = Field(..., ge=0)
    shots: list[ShotRead]


class PerformanceRoundBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    round_id: int
    course_id: int
    course_name: str
    started_at: datetime
    finished_at: datetime | None
    holes: list[PerformanceHoleBlock]


class PlayerPerformanceRead(BaseModel):
    player_id: int
    player_name: str
    rounds: list[PerformanceRoundBlock]
