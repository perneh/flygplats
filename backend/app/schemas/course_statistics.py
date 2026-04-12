from pydantic import BaseModel, ConfigDict, Field


class PlayerCourseStatisticsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_id: int
    player_name: str
    rounds_played: int = Field(..., ge=0)
    total_strokes: int = Field(..., ge=0)


class HoleActivityRow(BaseModel):
    """Aggregated shot counts per hole number on this course (all rounds)."""

    model_config = ConfigDict(extra="forbid")

    hole_number: int = Field(..., ge=1, le=18)
    total_strokes_recorded: int = Field(..., ge=0)


class CourseStatisticsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_id: int
    course_name: str
    total_rounds: int = Field(..., ge=0, description="Number of Round rows for this course")
    players: list[PlayerCourseStatisticsRow]
    holes: list[HoleActivityRow] = Field(
        default_factory=list,
        description="Per-hole shot totals across all rounds on this course",
    )
