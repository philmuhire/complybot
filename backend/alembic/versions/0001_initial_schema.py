"""Initial schema: incidents, agent_traces, regulations, evaluations

Revision ID: 0001
Revises:
Create Date: 2026-04-24
"""

from __future__ import annotations

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_input", sa.Text(), nullable=False),
        sa.Column("incident_type", sa.String(128), nullable=True),
        sa.Column("data_classification", sa.String(128), nullable=True),
        sa.Column("records_exposed", sa.Integer(), nullable=True),
        sa.Column("severity_score", sa.Float(), nullable=True),
        sa.Column("escalation_level", sa.String(64), nullable=True),
        sa.Column("regulator_notification_required", sa.Boolean(), nullable=True),
        sa.Column("deadline_hours", sa.Integer(), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("final_report", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "regulations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("framework", sa.String(128), nullable=False),
        sa.Column("clause_number", sa.String(128), nullable=False),
        sa.Column("source_document", sa.String(512), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("jurisdiction", sa.String(64), nullable=True),
        sa.Column("user_document_id", sa.String(36), nullable=True),
        sa.Column("owner_id", sa.String(128), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.create_index("ix_regulations_framework", "regulations", ["framework"])
    op.create_index("ix_regulations_jurisdiction", "regulations", ["jurisdiction"], unique=False)
    op.create_index("ix_regulations_user_document_id", "regulations", ["user_document_id"], unique=False)
    op.create_index("ix_regulations_owner_id", "regulations", ["owner_id"], unique=False)

    op.create_table(
        "agent_traces",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_name", sa.String(128), nullable=False),
        sa.Column("tool_called", sa.String(256), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("token_usage", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_traces_incident_id", "agent_traces", ["incident_id"])

    op.create_table(
        "evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hallucination_score", sa.Float(), nullable=True),
        sa.Column("citation_accuracy", sa.Float(), nullable=True),
        sa.Column("reasoning_score", sa.Float(), nullable=True),
        sa.Column("escalation_correctness", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evaluations_incident_id", "evaluations", ["incident_id"])


def downgrade() -> None:
    op.drop_index("ix_evaluations_incident_id", table_name="evaluations")
    op.drop_table("evaluations")
    op.drop_index("ix_agent_traces_incident_id", table_name="agent_traces")
    op.drop_table("agent_traces")
    op.drop_index("ix_regulations_owner_id", table_name="regulations")
    op.drop_index("ix_regulations_user_document_id", table_name="regulations")
    op.drop_index("ix_regulations_jurisdiction", table_name="regulations")
    op.drop_index("ix_regulations_framework", table_name="regulations")
    op.drop_table("regulations")
    op.drop_table("incidents")
