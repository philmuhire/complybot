"""Structured outputs for Agents SDK stages."""

from pydantic import BaseModel, Field


class LogIntelOutput(BaseModel):
    incident_type: str = Field(description="Normalized incident category")
    data_classification: str = Field(description="none | internal | personal_data | financial | health")
    records_exposed: int = Field(ge=0)
    systems_impacted: list[str]
    attack_vector: str
    timeline: str
    personal_data_involved: bool
    severity_hint: str = Field(description="low | medium | high | critical")


class RetrievalOutput(BaseModel):
    query_used: str
    regulatory_citations: list[dict] = Field(
        description="Each item: framework, clause_number, source_document, version, relevance_note"
    )
    jurisdiction_focus: str = Field(description="EU | US-FED | UK | OTHER")


class RiskOutput(BaseModel):
    severity_score: float = Field(ge=0, le=100)
    regulatory_exposure_score: float = Field(ge=0, le=100)
    operational_impact_score: float = Field(ge=0, le=100)
    confidence_level: float = Field(ge=0, le=1)
    rationale: str


class ObligationOutput(BaseModel):
    authority_notification_required: bool
    authority_deadline_hours: int | None
    user_notification_required: bool
    board_escalation_required: bool
    obligation_matrix: list[dict]


class EscalationOutput(BaseModel):
    level: str = Field(description="internal | ciso | executive | regulator_contact")
    rationale: str
    documentation_checklist: list[str]
    countdown_hours: int | None


class CriticOutput(BaseModel):
    passed: bool
    hallucination_risk: float = Field(ge=0, le=1)
    citation_accuracy_score: float = Field(ge=0, le=1)
    reasoning_score: float = Field(ge=0, le=1)
    escalation_correctness_score: float = Field(ge=0, le=1)
    missing_dimensions: list[str]
    retry_retrieval: bool
    refinement_instructions: str
