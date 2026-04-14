"""Add optional country on players (bundled init_data).

Revision ID: 007_player_country
Revises: 006_player_profile_fields
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa


revision = "007_player_country"
down_revision = "006_player_profile_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("players", sa.Column("country", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("players", "country")
