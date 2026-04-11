"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-04-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "holes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("par", sa.Integer(), nullable=False),
        sa.Column("tee_x", sa.Float(), nullable=False),
        sa.Column("tee_y", sa.Float(), nullable=False),
        sa.Column("green_x", sa.Float(), nullable=False),
        sa.Column("green_y", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "number", name="uq_hole_course_number"),
    )
    op.create_index(op.f("ix_holes_course_id"), "holes", ["course_id"], unique=False)
    op.create_table(
        "rounds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rounds_course_id"), "rounds", ["course_id"], unique=False)
    op.create_index(op.f("ix_rounds_player_id"), "rounds", ["player_id"], unique=False)
    op.create_table(
        "shots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("hole_id", sa.Integer(), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("club", sa.String(length=64), nullable=False),
        sa.Column("distance", sa.Float(), nullable=True),
        sa.Column("shot_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["hole_id"], ["holes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["round_id"], ["rounds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_shots_hole_id"), "shots", ["hole_id"], unique=False)
    op.create_index(op.f("ix_shots_round_id"), "shots", ["round_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_shots_round_id"), table_name="shots")
    op.drop_index(op.f("ix_shots_hole_id"), table_name="shots")
    op.drop_table("shots")
    op.drop_index(op.f("ix_rounds_player_id"), table_name="rounds")
    op.drop_index(op.f("ix_rounds_course_id"), table_name="rounds")
    op.drop_table("rounds")
    op.drop_index(op.f("ix_holes_course_id"), table_name="holes")
    op.drop_table("holes")
    op.drop_table("courses")
    op.drop_table("players")
