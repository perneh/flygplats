from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlayerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    handicap: float | None = Field(None, ge=0, le=54)
    age: int | None = Field(None, ge=1, le=120)
    gender: str | None = Field(None, min_length=1, max_length=32)
    email: str | None = Field(None, min_length=3, max_length=320)
    sponsor: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, min_length=3, max_length=64)
    country: str | None = Field(None, min_length=1, max_length=128)
    club: str | None = Field(None, min_length=1, max_length=255)
    rank: int | None = Field(None, ge=1, le=9999)


class PlayerCreate(PlayerBase):
    pass


class PlayerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    handicap: float | None = Field(None, ge=0, le=54)
    age: int | None = Field(None, ge=1, le=120)
    gender: str | None = Field(None, min_length=1, max_length=32)
    email: str | None = Field(None, min_length=3, max_length=320)
    sponsor: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, min_length=3, max_length=64)
    country: str | None = Field(None, min_length=1, max_length=128)
    club: str | None = Field(None, min_length=1, max_length=255)
    rank: int | None = Field(None, ge=1, le=9999)


class PlayerRead(PlayerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
