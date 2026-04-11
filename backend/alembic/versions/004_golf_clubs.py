"""Golf club catalog (reference data from init JSON).

Revision ID: 004_golf_clubs
Revises: 003_course_country_hole_geo
Create Date: 2026-04-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_golf_clubs"
down_revision: Union[str, None] = "003_course_country_hole_geo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "golf_clubs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("catalog_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("club_type", sa.String(length=64), nullable=False),
        sa.Column("loft_deg", sa.Float(), nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.Column("max_distance_m", sa.Integer(), nullable=False),
        sa.Column("avg_distance_m", sa.Integer(), nullable=False),
        sa.Column("player_levels", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("catalog_id", name="uq_golf_clubs_catalog_id"),
    )


def downgrade() -> None:
    op.drop_table("golf_clubs")
