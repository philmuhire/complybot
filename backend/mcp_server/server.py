"""FastMCP server — tools match agent contract; implementations delegate to ``ComplianceToolService``."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compliance_core.database import SessionLocal  # noqa: E402
from compliance_core.tool_service import ComplianceToolService  # noqa: E402

mcp = FastMCP("cyber-compliance-mcp")


@mcp.tool()
async def search_regulations(
    query: str,
    jurisdiction: str | None = None,
    framework: str | None = None,
) -> str:
    """
    RAG over regulation chunks. `jurisdiction` can be a single tag or comma‑separated tags
    to match indexed regulations (including multi‑tag rows); overlaps with the incident
    `jurisdictions` the pipeline passes you.
    """
    async with SessionLocal() as session:
        svc = ComplianceToolService(session)
        rows = await svc.search_regulations(query, jurisdiction=jurisdiction, framework=framework)
        return json.dumps(rows, ensure_ascii=False)


@mcp.tool()
async def get_incident_history(incident_id: str) -> str:
    async with SessionLocal() as session:
        svc = ComplianceToolService(session)
        data = await svc.get_incident_history(incident_id)
        return json.dumps(data, ensure_ascii=False)


@mcp.tool()
async def calculate_risk_score(params_json: str) -> str:
    params = json.loads(params_json or "{}")
    async with SessionLocal() as session:
        svc = ComplianceToolService(session)
        data = await svc.calculate_risk_score(params)
        return json.dumps(data, ensure_ascii=False)


@mcp.tool()
async def check_reporting_deadline(jurisdiction: str, incident_type: str) -> str:
    async with SessionLocal() as session:
        svc = ComplianceToolService(session)
        data = svc.check_reporting_deadline(jurisdiction, incident_type)
        return json.dumps(data, ensure_ascii=False)


@mcp.tool()
async def log_case_to_database(case_json: str) -> str:
    payload = json.loads(case_json or "{}")
    async with SessionLocal() as session:
        svc = ComplianceToolService(session)
        data = await svc.log_case_to_database(payload)
        return json.dumps(data, ensure_ascii=False)


@mcp.tool()
async def generate_notification_draft(case_json: str) -> str:
    payload = json.loads(case_json or "{}")
    async with SessionLocal() as session:
        svc = ComplianceToolService(session)
        data = await svc.generate_notification_draft(payload)
        return json.dumps(data, ensure_ascii=False)
