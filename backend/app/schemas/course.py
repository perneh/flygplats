from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    country: str | None = Field(None, max_length=128)
    description: str | None = None


class CourseCreate(CourseBase):
    #: Optional id from catalog JSON (unique when set).
    catalog_id: int | None = None


class CourseUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    country: str | None = Field(None, max_length=128)
    description: str | None = None
    catalog_id: int | None = None


class CourseRead(CourseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    catalog_id: int | None
    created_at: datetime
