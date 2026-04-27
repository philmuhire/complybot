from pydantic import BaseModel, Field, model_validator


class AnalyzeBody(BaseModel):
    raw_input: str = Field(min_length=10, description="Incident narrative and/or log excerpt")
    jurisdiction_hint: str | None = Field(
        default=None,
        max_length=256,
        description="Legacy single label; prefer `jurisdictions`.",
    )
    jurisdictions: list[str] = Field(
        default_factory=list,
        max_length=32,
        description="Regulation index tags (distinct values from the regulations table); at least one required.",
    )

    @model_validator(mode="after")
    def _ensure_jurisdictions(self) -> "AnalyzeBody":
        seen: set[str] = set()
        out: list[str] = []
        for j in self.jurisdictions or []:
            s = (j or "").strip()[:128]
            if not s:
                continue
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(s)
        if not out and self.jurisdiction_hint:
            for p in self.jurisdiction_hint.split(","):
                s = p.strip()[:128]
                if s and s.lower() not in seen:
                    seen.add(s.lower())
                    out.append(s)
        if not out:
            out = ["EU"]
        self.jurisdictions = out[:32]
        return self


class IncidentSummary(BaseModel):
    id: str
    created_at: str | None
    incident_type: str | None
    severity_score: float | None
    escalation_level: str | None
    status: str
    regulator_notification_required: bool | None
