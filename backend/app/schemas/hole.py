from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.schemas.latlng import LatLng


class HoleCreate(BaseModel):
    """
    Body aligned with ``golf_courses_25.json`` per hole: field ``hole`` (alias ``number``).

    Provide ``tee`` + ``green`` (WGS84), **or** omit both and send legacy ``tee_x`` / ``green_x`` only.
    """

    model_config = ConfigDict(populate_by_name=True)

    course_id: int
    hole: int = Field(..., ge=1, le=18, validation_alias=AliasChoices("hole", "number"))
    par: int = Field(4, ge=3, le=6)
    length_m: float | None = None
    tee: LatLng | None = None
    green: LatLng | None = None
    tee_x: float = 0.0
    tee_y: float = 0.0
    green_x: float = 100.0
    green_y: float = 0.0

    @model_validator(mode="after")
    def tee_green_together(self) -> HoleCreate:
        if (self.tee is None) ^ (self.green is None):
            raise ValueError("Provide both tee and green, or neither (legacy canvas coordinates).")
        return self


class HoleUpdate(BaseModel):
    number: int | None = Field(None, ge=1, le=18)
    par: int | None = Field(None, ge=3, le=6)
    length_m: float | None = None
    tee_lat: float | None = None
    tee_lng: float | None = None
    green_lat: float | None = None
    green_lng: float | None = None
    tee_x: float | None = None
    tee_y: float | None = None
    green_x: float | None = None
    green_y: float | None = None


class HoleRead(BaseModel):
    """JSON aligned with init data: ``hole``, ``tee`` / ``green``, plus flat canvas coordinates."""

    model_config = ConfigDict(from_attributes=False)

    id: int
    course_id: int
    hole: int
    par: int
    length_m: float | None
    tee: LatLng
    green: LatLng
    tee_x: float
    tee_y: float
    green_x: float
    green_y: float

    @classmethod
    def from_hole(cls, h: Any) -> HoleRead:
        tl = float(h.tee_lat) if h.tee_lat is not None else 0.0
        tln = float(h.tee_lng) if h.tee_lng is not None else 0.0
        gl = float(h.green_lat) if h.green_lat is not None else 0.0
        gln = float(h.green_lng) if h.green_lng is not None else 0.0
        return cls(
            id=h.id,
            course_id=h.course_id,
            hole=h.number,
            par=h.par,
            length_m=h.length_m,
            tee=LatLng(lat=tl, lng=tln),
            green=LatLng(lat=gl, lng=gln),
            tee_x=h.tee_x,
            tee_y=h.tee_y,
            green_x=h.green_x,
            green_y=h.green_y,
        )
