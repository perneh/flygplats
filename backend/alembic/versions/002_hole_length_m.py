"""Add holes.length_m for init data (course yardage).

Revision ID: 002_hole_length_m
Revises: 001_initial
Create Date: 2026-04-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_hole_length_m"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("holes", sa.Column("length_m", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("holes", "length_m")
