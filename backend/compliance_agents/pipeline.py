"""Multi-agent incident pipeline coordinated by the OpenAI Agents SDK + MCP tools."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from agents import (
    Agent,
    AgentOutputSchema,
    ModelSettings,
    OpenAIChatCompletionsModel,
    Runner,
    RunConfig,
)
from agents.mcp import MCPServerStdio
from agents.mcp.server import MCPServerStdioParams
from agents.mcp.manager import MCPServerManager

from backend.compliance_agents.instructions.compliance_retrieval import COMPLIANCE_RETRIEVAL_INSTRUCTIONS
from backend.compliance_agents.instructions.critic_auditor import CRITIC_AUDITOR_INSTRUCTIONS
from backend.compliance_agents.instructions.escalation_decision import ESCALATION_DECISION_INSTRUCTIONS
from backend.compliance_agents.instructions.log_intelligence import LOG_INTELLIGENCE_INSTRUCTIONS
from backend.compliance_agents.instructions.regulatory_obligation import REGULATORY_OBLIGATION_INSTRUCTIONS
from backend.compliance_agents.instructions.risk_scoring import RISK_SCORING_INSTRUCTIONS
from backend.compliance_agents.output_models import (
    CriticOutput,
    EscalationOutput,
    LogIntelOutput,
    ObligationOutput,
    RetrievalOutput,
    RiskOutput,
)
from compliance_core.config import get_settings
from compliance_core.jurisdictions import merge_jurisdiction_labels
from compliance_core.llm import get_agent_chat_model
from compliance_core.database import SessionLocal
from compliance_core.models import AgentTrace, Evaluation
from compliance_core.tool_service import ComplianceToolService

logger = logging.getLogger(__name__)

ROOT = _BACKEND_ROOT


def _output_schema(model_cls: type[Any]) -> AgentOutputSchema:
    """Structured outputs use list[dict] etc.; OpenAI strict JSON schema rejects those shapes."""
    return AgentOutputSchema(model_cls, strict_json_schema=False)

try:
    from langfuse import observe
except Exception:  # pragma: no cover

    def observe(*_a, **_k):
        def deco(fn):
            return fn

        return deco


def _parse_pipeline_jurisdictions(
    jurisdiction_hint: str | None,
    jurisdictions: list[str] | None,
) -> tuple[list[str], str]:
    merged = merge_jurisdiction_labels(
        jurisdiction=jurisdiction_hint,
        jurisdictions=jurisdictions,
    )
    jlist = [p.strip() for p in merged.split(",") if p.strip()] if merged else []
    if not jlist:
        jlist = ["EU"]
    return jlist, jlist[0]


def _mcp_stdio_server() -> MCPServerStdio:
    env = {**os.environ}
    py_path = env.get("PYTHONPATH", "")
    backend_dir = str(ROOT)
    if backend_dir not in py_path.split(os.pathsep):
        env["PYTHONPATH"] = (
            f"{backend_dir}{os.pathsep}{py_path}" if py_path.strip() else backend_dir
        )
    params: MCPServerStdioParams = {
        "command": sys.executable,
        "args": ["-m", "mcp_server"],
        "cwd": str(ROOT),
        "env": env,
    }
    return MCPServerStdio(
        params,
        name="cyber-compliance-mcp",
        client_session_timeout_seconds=120,
        cache_tools_list=True,
    )


def _model_settings() -> ModelSettings:
    return ModelSettings(temperature=0.1, top_p=1)


def _trace_run_config() -> RunConfig:
    """Send traces to OpenAI platform using OPENAI_API_KEY only (not OpenRouter chat key)."""
    s = get_settings()
    tracing = {"api_key": s.openai_api_key} if s.openai_api_key else None
    return RunConfig(
        workflow_name="Compliance incident pipeline",
        tracing=tracing,
    )


def _build_agents(
    mcp_servers: list, chat_model: OpenAIChatCompletionsModel
) -> dict[str, Agent]:
    ms = _model_settings()
    return {
        "log": Agent(
            name="LogIntelligence",
            instructions=LOG_INTELLIGENCE_INSTRUCTIONS,
            model=chat_model,
            model_settings=ms,
            output_type=_output_schema(LogIntelOutput),
        ),
        "retrieval": Agent(
            name="ComplianceRetrieval",
            instructions=COMPLIANCE_RETRIEVAL_INSTRUCTIONS,
            model=chat_model,
            model_settings=ms,
            mcp_servers=mcp_servers,
            output_type=_output_schema(RetrievalOutput),
        ),
        "risk": Agent(
            name="RiskScoring",
            instructions=RISK_SCORING_INSTRUCTIONS,
            model=chat_model,
            model_settings=ms,
            mcp_servers=mcp_servers,
            output_type=_output_schema(RiskOutput),
        ),
        "obligation": Agent(
            name="RegulatoryObligation",
            instructions=REGULATORY_OBLIGATION_INSTRUCTIONS,
            model=chat_model,
            model_settings=ms,
            mcp_servers=mcp_servers,
            output_type=_output_schema(ObligationOutput),
        ),
        "escalation": Agent(
            name="EscalationDecision",
            instructions=ESCALATION_DECISION_INSTRUCTIONS,
            model=chat_model,
            model_settings=ms,
            output_type=_output_schema(EscalationOutput),
        ),
        "critic": Agent(
            name="CriticAuditor",
            instructions=CRITIC_AUDITOR_INSTRUCTIONS,
            model=chat_model,
            model_settings=ms,
            output_type=_output_schema(CriticOutput),
        ),
    }


async def _trace(
    incident_id: str,
    agent_name: str,
    summary: str,
    *,
    tool_hint: str | None = None,
    latency_ms: float | None = None,
    token_usage: dict | None = None,
) -> None:
    async with SessionLocal() as session:
        session.add(
            AgentTrace(
                incident_id=incident_id,
                agent_name=agent_name,
                tool_called=tool_hint,
                latency_ms=latency_ms,
                token_usage=token_usage,
                output_summary=summary[:24000],
            )
        )
        await session.commit()


async def _run_agent(
    label: str, agent: Agent, payload: str, incident_id: str
) -> Any:
    t0 = time.perf_counter()
    result = await Runner.run(
        agent,
        payload,
        max_turns=25,
        run_config=_trace_run_config(),
    )
    elapsed = (time.perf_counter() - t0) * 1000
    await _trace(
        incident_id,
        label,
        str(result.final_output),
        latency_ms=elapsed,
        token_usage=None,
    )
    return result.final_output


@observe(name="incident_pipeline")
async def run_incident_pipeline(
    *,
    incident_id: str,
    raw_input: str,
    jurisdictions: list[str] | None = None,
    jurisdiction_hint: str | None = None,
) -> dict[str, Any]:
    """Execute the full governance pipeline with MCP-backed tools."""
    jlist, j_primary = _parse_pipeline_jurisdictions(jurisdiction_hint, jurisdictions)
    filter_csv = merge_jurisdiction_labels(jurisdiction=None, jurisdictions=jlist) or "EU"
    bundle: dict[str, Any] = {
        "incident_id": incident_id,
        "jurisdictions": jlist,
        "jurisdiction_hint": j_primary,
        "jurisdiction_filter_csv": filter_csv,
    }

    chat_model = get_agent_chat_model()

    async with MCPServerManager([_mcp_stdio_server()], strict=True) as mcm:
        agents = _build_agents(mcm.active_servers, chat_model)

        log_out = await _run_agent(
            "LogIntelligence",
            agents["log"],
            json.dumps({"incident_id": incident_id, "raw_input": raw_input}),
            incident_id,
        )
        bundle["log_intelligence"] = log_out.model_dump()

        retrieval_in = json.dumps(
            {
                "incident_id": incident_id,
                "log_intelligence": bundle["log_intelligence"],
                "jurisdictions": jlist,
                "jurisdiction_hint": j_primary,
                "regulation_jurisdiction_filter": filter_csv,
            }
        )
        retrieval_out = await _run_agent(
            "ComplianceRetrieval", agents["retrieval"], retrieval_in, incident_id
        )
        bundle["retrieval"] = retrieval_out.model_dump()

        risk_params = {
            "severity_hint": bundle["log_intelligence"]["severity_hint"],
            "records_exposed": bundle["log_intelligence"]["records_exposed"],
            "personal_data_involved": bundle["log_intelligence"]["personal_data_involved"],
            "regulatory_clauses_hit": len(bundle["retrieval"]["regulatory_citations"]),
        }
        risk_in = json.dumps(
            {
                "incident_id": incident_id,
                "log_intelligence": bundle["log_intelligence"],
                "retrieval": bundle["retrieval"],
                "risk_tool_inputs": risk_params,
            }
        )
        risk_out = await _run_agent("RiskScoring", agents["risk"], risk_in, incident_id)
        bundle["risk"] = risk_out.model_dump()

        obl_in = json.dumps(
            {
                "incident_id": incident_id,
                "log_intelligence": bundle["log_intelligence"],
                "retrieval": bundle["retrieval"],
                "risk": bundle["risk"],
                "jurisdiction": j_primary,
                "jurisdictions": jlist,
                "incident_type": bundle["log_intelligence"]["incident_type"],
            }
        )
        obl_out = await _run_agent(
            "RegulatoryObligation", agents["obligation"], obl_in, incident_id
        )
        bundle["obligations"] = obl_out.model_dump()

        esc_in = json.dumps(
            {
                "incident_id": incident_id,
                "log_intelligence": bundle["log_intelligence"],
                "risk": bundle["risk"],
                "obligations": bundle["obligations"],
            }
        )
        esc_out = await _run_agent(
            "EscalationDecision", agents["escalation"], esc_in, incident_id
        )
        bundle["escalation"] = esc_out.model_dump()

        critic_in = json.dumps({"incident_id": incident_id, "bundle": bundle})
        critic_out: CriticOutput = await _run_agent(
            "CriticAuditor", agents["critic"], critic_in, incident_id
        )
        bundle["critic"] = critic_out.model_dump()

        if critic_out.retry_retrieval:
            refined = json.dumps(
                {
                    "incident_id": incident_id,
                    "log_intelligence": bundle["log_intelligence"],
                    "refinement_instructions": critic_out.refinement_instructions,
                    "previous_retrieval": bundle["retrieval"],
                    "jurisdictions": jlist,
                    "jurisdiction_hint": j_primary,
                    "regulation_jurisdiction_filter": filter_csv,
                }
            )
            retrieval_out = await _run_agent(
                "ComplianceRetrievalRefined",
                agents["retrieval"],
                refined,
                incident_id,
            )
            bundle["retrieval"] = retrieval_out.model_dump()
            critic_in2 = json.dumps({"incident_id": incident_id, "bundle": bundle})
            critic_out = await _run_agent(
                "CriticAuditorSecondPass", agents["critic"], critic_in2, incident_id
            )
            bundle["critic"] = critic_out.model_dump()

        hours = bundle["obligations"].get("authority_deadline_hours")
        deadline_hours = int(hours) if hours is not None else None

        final_report = {
            "incident_type": bundle["log_intelligence"]["incident_type"],
            "personal_data_involved": bundle["log_intelligence"]["personal_data_involved"],
            "severity_score": bundle["risk"]["severity_score"],
            "obligations": bundle["obligations"],
            "escalation": bundle["escalation"],
            "critic_passed": bundle["critic"]["passed"],
        }

        async with SessionLocal() as session:
            svc = ComplianceToolService(session)
            await svc.log_case_to_database(
                {
                    "incident_id": incident_id,
                    "raw_input": raw_input,
                    "incident_type": bundle["log_intelligence"]["incident_type"],
                    "data_classification": bundle["log_intelligence"]["data_classification"],
                    "records_exposed": bundle["log_intelligence"]["records_exposed"],
                    "severity_score": bundle["risk"]["severity_score"],
                    "escalation_level": bundle["escalation"]["level"],
                    "regulator_notification_required": bundle["obligations"][
                        "authority_notification_required"
                    ],
                    "deadline_hours": deadline_hours,
                    "confidence_score": bundle["risk"]["confidence_level"],
                    "final_report": {"pipeline": bundle},
                    "status": "completed" if critic_out.passed else "needs_review",
                }
            )

            ev = Evaluation(
                incident_id=incident_id,
                hallucination_score=critic_out.hallucination_risk,
                citation_accuracy=critic_out.citation_accuracy_score,
                reasoning_score=critic_out.reasoning_score,
                escalation_correctness=critic_out.escalation_correctness_score,
                notes=json.dumps(
                    {
                        "missing_dimensions": critic_out.missing_dimensions,
                        "retry_retrieval": critic_out.retry_retrieval,
                    }
                ),
            )
            session.add(ev)
            await session.commit()

        return {"ok": True, "incident_id": incident_id, "pipeline": bundle}


def run_incident_pipeline_sync(**kwargs: Any) -> dict[str, Any]:
    return asyncio.run(run_incident_pipeline(**kwargs))
