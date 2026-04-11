from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RoundBase(BaseModel):
    player_id: int
    course_id: int


class RoundCreate(RoundBase):
    pass


class RoundUpdate(BaseModel):
    finished_at: datetime | None = None


class RoundRead(RoundBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    finished_at: datetime | None
