"""Store original uploaded file bytes for framework documents

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "framework_document_originals",
        sa.Column("user_document_id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("owner_id", sa.String(128), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(256), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
    )
    op.create_index(
        "ix_framework_document_originals_owner_id",
        "framework_document_originals",
        ["owner_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_framework_document_originals_owner_id", table_name="framework_document_originals")
    op.drop_table("framework_document_originals")
