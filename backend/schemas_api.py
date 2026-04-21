from pydantic import BaseModel, Field


class AnalyzeBody(BaseModel):
    raw_input: str = Field(min_length=10, description="Incident narrative and/or log excerpt")
    jurisdiction_hint: str = Field(default="EU", description="EU, US-FED, UK, OTHER")


class IncidentSummary(BaseModel):
    id: str
    created_at: str | None
    incident_type: str | None
    severity_score: float | None
    escalation_level: str | None
    status: str
    regulator_notification_required: bool | None
