"""Tournaments, flights, and scorecards.

Revision ID: 005_tournaments
Revises: 004_golf_clubs
Create Date: 2026-04-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_tournaments"
down_revision: Union[str, None] = "004_golf_clubs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tournaments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("play_date", sa.Date(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tournaments_course_id"), "tournaments", ["course_id"], unique=False)

    op.create_table(
        "tournament_participants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("handicap", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tournament_id", "player_id", name="uq_tournament_player"),
    )
    op.create_index(
        op.f("ix_tournament_participants_player_id"),
        "tournament_participants",
        ["player_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tournament_participants_tournament_id"),
        "tournament_participants",
        ["tournament_id"],
        unique=False,
    )

    op.create_table(
        "tournament_flights",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tournament_id", "sequence", name="uq_tournament_flight_seq"),
    )
    op.create_index(
        op.f("ix_tournament_flights_tournament_id"),
        "tournament_flights",
        ["tournament_id"],
        unique=False,
    )

    op.create_table(
        "scorecards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("flight_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["flight_id"], ["tournament_flights.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tournament_id", "player_id", name="uq_scorecard_tournament_player"),
    )
    op.create_index(op.f("ix_scorecards_flight_id"), "scorecards", ["flight_id"], unique=False)
    op.create_index(op.f("ix_scorecards_player_id"), "scorecards", ["player_id"], unique=False)
    op.create_index(
        op.f("ix_scorecards_tournament_id"), "scorecards", ["tournament_id"], unique=False
    )

    op.create_table(
        "hole_scores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scorecard_id", sa.Integer(), nullable=False),
        sa.Column("hole_number", sa.Integer(), nullable=False),
        sa.Column("strokes", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["scorecard_id"], ["scorecards.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scorecard_id", "hole_number", name="uq_hole_score_card_hole"),
    )
    op.create_index(op.f("ix_hole_scores_scorecard_id"), "hole_scores", ["scorecard_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_hole_scores_scorecard_id"), table_name="hole_scores")
    op.drop_table("hole_scores")
    op.drop_index(op.f("ix_scorecards_tournament_id"), table_name="scorecards")
    op.drop_index(op.f("ix_scorecards_player_id"), table_name="scorecards")
    op.drop_index(op.f("ix_scorecards_flight_id"), table_name="scorecards")
    op.drop_table("scorecards")
    op.drop_index(op.f("ix_tournament_flights_tournament_id"), table_name="tournament_flights")
    op.drop_table("tournament_flights")
    op.drop_index(op.f("ix_tournament_participants_tournament_id"), table_name="tournament_participants")
    op.drop_index(op.f("ix_tournament_participants_player_id"), table_name="tournament_participants")
    op.drop_table("tournament_participants")
    op.drop_index(op.f("ix_tournaments_course_id"), table_name="tournaments")
    op.drop_table("tournaments")
