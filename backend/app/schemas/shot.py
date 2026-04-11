from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShotBase(BaseModel):
    x: float
    y: float
    club: str = Field("", max_length=64)
    distance: float | None = None


class ShotCreate(ShotBase):
    round_id: int
    hole_id: int


class ShotUpdate(BaseModel):
    x: float | None = None
    y: float | None = None
    club: str | None = Field(None, max_length=64)
    distance: float | None = None
    shot_at: datetime | None = None


class ShotRead(ShotBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    round_id: int
    hole_id: int
    shot_at: datetime
