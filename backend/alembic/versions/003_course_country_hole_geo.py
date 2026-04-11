"""Course country + catalog id; hole WGS84 coordinates for init JSON alignment.

Revision ID: 003_course_country_hole_geo
Revises: 002_hole_length_m
Create Date: 2026-04-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_course_country_hole_geo"
down_revision: Union[str, None] = "002_hole_length_m"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("country", sa.String(length=128), nullable=True))
    op.add_column(
        "courses",
        sa.Column("catalog_id", sa.Integer(), nullable=True),
    )
    op.create_unique_constraint("uq_courses_catalog_id", "courses", ["catalog_id"])

    op.add_column("holes", sa.Column("tee_lat", sa.Float(), nullable=True))
    op.add_column("holes", sa.Column("tee_lng", sa.Float(), nullable=True))
    op.add_column("holes", sa.Column("green_lat", sa.Float(), nullable=True))
    op.add_column("holes", sa.Column("green_lng", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("holes", "green_lng")
    op.drop_column("holes", "green_lat")
    op.drop_column("holes", "tee_lng")
    op.drop_column("holes", "tee_lat")
    op.drop_constraint("uq_courses_catalog_id", "courses", type_="unique")
    op.drop_column("courses", "catalog_id")
    op.drop_column("courses", "country")
