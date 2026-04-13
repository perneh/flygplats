from pydantic import BaseModel, ConfigDict, Field


class PlayerHoleStatisticsRow(BaseModel):
    """Per-player shot count on a single hole (all rounds on this course)."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    player_name: str
    strokes_on_hole: int = Field(..., ge=0)


class HoleStatisticsRead(BaseModel):
    """Aggregated activity for one hole on a course (shots and rounds)."""

    model_config = ConfigDict(extra="forbid")

    course_id: int
    course_name: str
    hole_id: int
    hole_number: int = Field(..., ge=1, le=18)
    par: int = Field(..., ge=3, le=6)
    total_strokes_recorded: int = Field(..., ge=0)
    rounds_with_shots_on_hole: int = Field(
        ...,
        ge=0,
        description="Distinct rounds that have at least one shot on this hole",
    )
    players: list[PlayerHoleStatisticsRow]
