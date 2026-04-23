from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from compliance_core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    raw_input: Mapped[str] = mapped_column(Text)
    incident_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    data_classification: Mapped[str | None] = mapped_column(String(128), nullable=True)
    records_exposed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    escalation_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    regulator_notification_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    deadline_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    final_report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    traces: Mapped[list["AgentTrace"]] = relationship(back_populates="incident")
    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="incident")


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    agent_name: Mapped[str] = mapped_column(String(128))
    tool_called: Mapped[str | None] = mapped_column(String(256), nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    token_usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    incident: Mapped["Incident"] = relationship(back_populates="traces")


class Regulation(Base):
    __tablename__ = "regulations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    framework: Mapped[str] = mapped_column(String(128), index=True)
    clause_number: Mapped[str] = mapped_column(String(128))
    source_document: Mapped[str] = mapped_column(String(512))
    version: Mapped[str] = mapped_column(String(64))
    jurisdiction: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    user_document_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    owner_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    text: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1536), nullable=True)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    hallucination_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    citation_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasoning_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    escalation_correctness: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    incident: Mapped["Incident"] = relationship(back_populates="evaluations")
