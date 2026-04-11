from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlayerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class PlayerCreate(PlayerBase):
    pass


class PlayerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)


class PlayerRead(PlayerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
