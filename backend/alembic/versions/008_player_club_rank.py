"""Add optional club and rank on players.

Revision ID: 008_player_club_rank
Revises: 007_player_country
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa


revision = "008_player_club_rank"
down_revision = "007_player_country"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("players", sa.Column("club", sa.String(length=255), nullable=True))
    op.add_column("players", sa.Column("rank", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("players", "rank")
    op.drop_column("players", "club")
