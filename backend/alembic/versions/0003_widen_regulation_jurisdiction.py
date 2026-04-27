"""Widen regulations.jurisdiction for CSV multi-tag values

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "regulations",
        "jurisdiction",
        existing_type=sa.String(64),
        type_=sa.String(256),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "regulations",
        "jurisdiction",
        existing_type=sa.String(256),
        type_=sa.String(64),
        existing_nullable=True,
    )
