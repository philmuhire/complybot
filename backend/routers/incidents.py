import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import clerk_user
from backend.schemas_api import AnalyzeBody, IncidentSummary
from backend.compliance_agents.pipeline import run_incident_pipeline
from compliance_core.database import get_session
from compliance_core.models import AgentTrace, Incident

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentSummary])
async def list_incidents(
    session: AsyncSession = Depends(get_session),
    _user: dict = Depends(clerk_user),
):
    rows = (
        await session.execute(
            select(Incident).order_by(Incident.created_at.desc()).limit(100)
        )
    ).scalars().all()
    return [
        IncidentSummary(
            id=r.id,
            created_at=r.created_at.isoformat() if r.created_at else None,
            incident_type=r.incident_type,
            severity_score=r.severity_score,
            escalation_level=r.escalation_level,
            status=r.status,
            regulator_notification_required=r.regulator_notification_required,
        )
        for r in rows
    ]


@router.get("/{incident_id}")
async def get_incident(
    incident_id: str,
    session: AsyncSession = Depends(get_session),
    _user: dict = Depends(clerk_user),
):
    inc = await session.get(Incident, incident_id)
    if not inc:
        raise HTTPException(404, "Incident not found")
    traces = (
        await session.execute(select(AgentTrace).where(AgentTrace.incident_id == incident_id))
    ).scalars().all()
    return {
        "incident": {
            "id": inc.id,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
            "status": inc.status,
            "raw_input": inc.raw_input,
            "final_report": inc.final_report,
            "severity_score": inc.severity_score,
            "escalation_level": inc.escalation_level,
            "regulator_notification_required": inc.regulator_notification_required,
            "deadline_at": inc.deadline_at.isoformat() if inc.deadline_at else None,
            "confidence_score": inc.confidence_score,
        },
        "traces": [
            {
                "agent_name": t.agent_name,
                "latency_ms": t.latency_ms,
                "output_summary": (t.output_summary or "")[:4000],
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in traces
        ],
    }


@router.post("/analyze")
async def analyze_incident(
    body: AnalyzeBody,
    session: AsyncSession = Depends(get_session),
    _user: dict = Depends(clerk_user),
):
    incident_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    session.add(
        Incident(
            id=incident_id,
            raw_input=body.raw_input,
            status="processing",
            created_at=now,
        )
    )
    await session.commit()

    try:
        result = await run_incident_pipeline(
            incident_id=incident_id,
            raw_input=body.raw_input,
            jurisdictions=body.jurisdictions,
            jurisdiction_hint=body.jurisdiction_hint,
        )
    except Exception as exc:
        inc = await session.get(Incident, incident_id)
        if inc:
            inc.status = "failed"
            await session.commit()
        raise HTTPException(500, detail=str(exc)) from exc

    return result
