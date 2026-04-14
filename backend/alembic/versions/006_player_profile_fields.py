"""Add optional player profile fields.

Revision ID: 006_player_profile_fields
Revises: 005_tournaments
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "006_player_profile_fields"
down_revision = "005_tournaments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("players", sa.Column("handicap", sa.Float(), nullable=True))
    op.add_column("players", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("players", sa.Column("gender", sa.String(length=32), nullable=True))
    op.add_column("players", sa.Column("email", sa.String(length=320), nullable=True))
    op.add_column("players", sa.Column("sponsor", sa.String(length=255), nullable=True))
    op.add_column("players", sa.Column("phone", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("players", "phone")
    op.drop_column("players", "sponsor")
    op.drop_column("players", "email")
    op.drop_column("players", "gender")
    op.drop_column("players", "age")
    op.drop_column("players", "handicap")
