# Compliance Governance Console — User Guide

## Who this is for

Security operations, GRC, privacy, and legal liaison teams assessing whether a cybersecurity event triggers **reporting obligations**, **internal escalation**, and **documentation duties** across illustrative NIST CSF / ISO 27001 / ENISA / GDPR-style sources plus internal policy snippets.

This product is **decision-support**, not legal advice. Counsel must validate conclusions before filings.

## Getting access

1. Navigate to your deployed URL (local: `http://localhost:3000`).
2. **Sign up** or **Sign in** via Clerk.
3. Open **`/Dashboard`** after authentication.

## Submitting an incident

1. Paste **raw logs**, SIEM excerpts, IAM trails, ticket narratives, or executive summaries into **Incident intake**.
2. Choose a **jurisdiction hint** (EU / US-style / UK / Other). This steers retrieval and deadline tooling — it does not replace legal jurisdiction analysis.
3. Click **Run governance pipeline**.

### What happens

The orchestrator executes specialist agents in sequence:

- Facts extraction → regulatory retrieval (with citations) → risk scoring → obligations matrix → escalation recommendation → critic audit (+ optional retrieval retry) → persisted case record.

Expect **30–90+ seconds** depending on model latency and MCP round-trips.

## Reading results

After a successful run:

- The **JSON panel** shows the full structured bundle (log intel, citations, risk, obligations, escalation, critic scores).
- The **Registry** lists historical cases stored in PostgreSQL.
- Selecting a case shows **agent traces** (structured outputs per agent stage).

### Key fields to validate manually

| Question | Where to look |
|----------|----------------|
| Was personal data involved? | `pipeline.log_intelligence.personal_data_involved` |
| Mandatory reporting? | `pipeline.obligations.authority_notification_required` |
| Deadline window (illustrative)? | `pipeline.obligations.authority_deadline_hours` + tool-backed rules |
| Controls suspected weak? | Narrative + risk rationale + obligations matrix rows |
| Penalties / exposure (illustrative)? | Risk scores + citations — **not** definitive fines |

## Interpreting critic scores

The critic emits **hallucination risk** (lower is better) and **citation accuracy**. If **`retry_retrieval`** fired, the engine performed a second retrieval pass using your refinement hints.

Cases marked `needs_review` failed critic pass thresholds — escalate to humans before external communication.

## Troubleshooting

| Symptom | Check |
|---------|-------|
| API 401 | Ensure repo-root `.env` has `CLERK_JWKS_URL`, `NEXT_PUBLIC_CLERK_*`, `CLERK_SECRET_KEY`; sign in so the browser sends a Bearer token |
| MCP / tool errors | API logs; verify DB running; MCP child process uses `PYTHONPATH` including `backend/` |
| Empty RAG hits | Run `python backend/scripts/seed_db.py` from the repo root |

## Responsible use

Log retention, lawful monitoring, and sector-specific duties vary. Always align outputs with organizational policies and regional law.
