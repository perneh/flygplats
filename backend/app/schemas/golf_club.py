from pydantic import BaseModel, ConfigDict, Field


class GolfClubCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalog_id: int | None = None
    name: str = Field(..., min_length=1, max_length=128)
    club_type: str = Field(..., max_length=64, validation_alias="type")
    loft_deg: float
    difficulty: str = Field(..., max_length=32)
    max_distance_m: int
    avg_distance_m: int
    player_levels: list[str] = Field(..., validation_alias="player_level")


class GolfClubRead(BaseModel):
    """API shape mirrors bundled JSON keys ``type`` and ``player_level``."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    catalog_id: int | None
    name: str
    club_type: str = Field(serialization_alias="type")
    loft_deg: float
    difficulty: str
    max_distance_m: int
    avg_distance_m: int
    player_levels: list[str] = Field(serialization_alias="player_level")


class GolfClubUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1, max_length=128)
    club_type: str | None = Field(None, max_length=64, validation_alias="type")
    loft_deg: float | None = None
    difficulty: str | None = Field(None, max_length=32)
    max_distance_m: int | None = None
    avg_distance_m: int | None = None
    player_levels: list[str] | None = Field(None, validation_alias="player_level")
