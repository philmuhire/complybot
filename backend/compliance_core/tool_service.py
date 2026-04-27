"""All MCP-exposed operations — sole DB boundary for agents."""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from compliance_core.models import Incident
from compliance_core.rag import hybrid_search
from compliance_core.rules import resolve_deadline_rule, risk_formula


class ComplianceToolService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_regulations(
        self,
        query: str,
        jurisdiction: str | None = None,
        jurisdictions: list[str] | None = None,
        framework: str | None = None,
    ) -> list[dict]:
        return await hybrid_search(
            self.session,
            query,
            jurisdiction=jurisdiction,
            jurisdictions=jurisdictions,
            framework=framework,
        )

    async def get_incident_history(self, incident_id: str) -> dict[str, Any]:
        row = await self.session.get(Incident, incident_id)
        if not row:
            return {"found": False, "incident_id": incident_id}
        return {
            "found": True,
            "incident_id": row.id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "severity_score": row.severity_score,
            "escalation_level": row.escalation_level,
            "status": row.status,
            "regulator_notification_required": row.regulator_notification_required,
            "deadline_at": row.deadline_at.isoformat() if row.deadline_at else None,
        }

    async def calculate_risk_score(self, params: dict[str, Any]) -> dict[str, Any]:
        severity = str(params.get("severity_hint") or "medium")
        records = int(params.get("records_exposed") or 0)
        personal = bool(params.get("personal_data_involved"))
        clauses = int(params.get("regulatory_clauses_hit") or 0)
        scores = risk_formula(
            severity_hint=severity,
            records_exposed=records,
            personal_data=personal,
            regulatory_clauses_hit=clauses,
        )
        return {"ok": True, **scores, "inputs": params}

    def check_reporting_deadline(self, jurisdiction: str, incident_type: str) -> dict[str, Any]:
        rule = resolve_deadline_rule(jurisdiction, incident_type)
        return {"jurisdiction": jurisdiction, "incident_type": incident_type, **rule}

    async def log_case_to_database(self, case_data: dict[str, Any]) -> dict[str, Any]:
        incident_id = case_data.get("incident_id")
        if not incident_id:
            return {"ok": False, "error": "incident_id required"}
        inc = await self.session.get(Incident, incident_id)
        now = datetime.now(timezone.utc)
        if inc is None:
            inc = Incident(id=incident_id, raw_input=case_data.get("raw_input") or "", status="processing")
            self.session.add(inc)

        inc.raw_input = case_data.get("raw_input", inc.raw_input)
        inc.incident_type = case_data.get("incident_type", inc.incident_type)
        inc.data_classification = case_data.get("data_classification", inc.data_classification)
        if case_data.get("records_exposed") is not None:
            inc.records_exposed = int(case_data["records_exposed"])
        if case_data.get("severity_score") is not None:
            inc.severity_score = float(case_data["severity_score"])
        if case_data.get("escalation_level") is not None:
            inc.escalation_level = str(case_data["escalation_level"])
        if case_data.get("regulator_notification_required") is not None:
            inc.regulator_notification_required = bool(case_data["regulator_notification_required"])
        if case_data.get("deadline_hours") is not None:
            inc.deadline_hours = int(case_data["deadline_hours"])
            inc.deadline_at = now + timedelta(hours=inc.deadline_hours)
        if case_data.get("confidence_score") is not None:
            inc.confidence_score = float(case_data["confidence_score"])
        if case_data.get("final_report") is not None:
            inc.final_report = case_data["final_report"]
        if case_data.get("status") is not None:
            inc.status = str(case_data["status"])

        await self.session.commit()
        return {"ok": True, "incident_id": incident_id}

    async def generate_notification_draft(self, case_data: dict[str, Any]) -> dict[str, Any]:
        report = case_data.get("final_report") or {}
        oblig = report.get("obligations") or {}
        esc = report.get("escalation") or {}
        draft = (
            "Subject: Regulatory / stakeholder notification — security incident reference "
            f"{case_data.get('incident_id', 'N/A')}\n\n"
            "Summary:\n"
            f"- Incident type: {report.get('incident_type', 'unknown')}\n"
            f"- Personal data involved: {report.get('personal_data_involved', 'unknown')}\n"
            f"- Severity score: {report.get('severity_score', 'n/a')}\n"
            f"- Authority notification: {oblig.get('authority_notification_required', 'n/a')}\n"
            f"- Deadline (hours): {oblig.get('authority_deadline_hours', 'n/a')}\n"
            f"- Escalation: {esc.get('level', 'n/a')}\n\n"
            "Next steps:\n"
            "1. Validate all citations against source instruments with legal counsel.\n"
            "2. Complete factual accuracy review with IR and data owners.\n"
            "3. File within the stated window if duty exists.\n"
        )
        return {"ok": True, "draft_text": draft, "format": "plain_text"}
