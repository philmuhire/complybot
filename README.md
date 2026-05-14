# Autonomous Cybersecurity Compliance & Incident Escalation AI

[Live Production](https://dsndxudm7ut8b.cloudfront.net/)

Autonomous Cybersecurity Compliance & Incident Escalation AI — a multi-agent platform that takes security incidents (logs/narratives), runs them through specialized AI agents, and helps with compliance, risk, reporting deadlines, and escalation using RAG over regulations (e.g. GDPR-style, NIST CSF, ISO 27001, ENISA, internal policy).

Multi-agent governance engine: FastAPI + OpenAI Agents SDK + MCP stdio tools + PostgreSQL/pgvector + Next.js dashboard (Clerk, TanStack Query, Zustand) + Observability(OpenAI Agents SDK traces + Langfuse) + GitHub Actions CI/CD + Production deployment on AWS.

## Architecture

1. **Log Intelligence Agent** — structured incident facts from raw logs/narratives.
2. **Compliance Retrieval Agent** — hybrid RAG (`pgvector` + lexical) over embedded regulations (GDPR-style, NIST CSF, ISO 27001, ENISA, internal policy excerpt).
3. **Risk Scoring Agent** — combines deterministic MCP `calculate_risk_score` + narrative rationale.
4. **Regulatory Obligation Agent** — MCP `check_reporting_deadline` + obligation matrix.
5. **Escalation Decision Agent** — escalation ladder + checklist + countdown.
6. **Critic / Auditor Agent** — hallucination/citation/deadline checks with optional retrieval retry.

All database access for agents flows through **`ComplianceToolService`** exposed as **MCP tools** (`backend/mcp_server`). The orchestrator persists final cases via the same service implementation after the critic gate (same code path as MCP `log_case_to_database`).

Observability hooks: OpenAI Agents SDK traces + optional **Langfuse** (`@observe` on `run_incident_pipeline`) when keys are present.

## Prerequisites

- Docker (for Postgres + pgvector)
- Python **3.10+** (project tested with 3.14 locally)
- Node.js **20+**
- OpenAI API key (agents + embeddings)
- Clerk application — **required** env keys (see `.env.example`): publishable key, secret, JWKS URL for API
- Optional: Langfuse keys

## Quick start

### 1. Database

The app expects **PostgreSQL with the [`pgvector`](https://github.com/pgvector/pgvector) extension**. Stock Postgres installers often **do not** include it—either use the Compose image below or install pgvector on your server.

```bash
docker compose up -d
cp .env.example .env
# Set `SUPABASE_DATABASE_URL` in `.env` to match Compose (default user/db/password from `docker-compose.yml`):
# postgresql+asyncpg://compliance:compliance@localhost:5432/compliance
```

If `seed_db` fails with **extension "vector" is not available**, your `SUPABASE_DATABASE_URL` is pointing at Postgres **without** pgvector; fix the URL or install the extension on that server.

Create schema + seed regulation embeddings:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python backend/scripts/seed_db.py
```

### 2. API

```bash
source .venv/bin/activate
export PYTHONPATH=.
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Health: `GET http://localhost:8000/health`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Put Clerk keys and URLs in the **repo-root** `.env` (same file as the backend); Next.js loads `../.env` automatically. Optional: copy root `.env` to `frontend/.env.local` if you prefer local overrides only.

Open `http://localhost:3000`, sign in, use **`/Dashboard`** to submit incidents.

### 4. Evaluation dataset (offline)

```bash
python backend/scripts/generate_synthetic_dataset.py
PYTHONPATH=. python backend/scripts/evaluate.py              # stub metrics
PYTHONPATH=. python backend/scripts/evaluate.py --live      # first 5 cases via live pipeline (needs keys + DB)
```

## Environment reference

| Variable | Purpose |
|----------|---------|
| `SUPABASE_DATABASE_URL` | **Required** — `postgresql+asyncpg://…` (only database URL; used by the API and by Alembic) |
| `OPENROUTER_API_KEY` | Primary key for chat + embeddings (`AsyncOpenAI` → OpenRouter) |
| `OPENROUTER_BASE_URL` | Default `https://openrouter.ai/api/v1` |
| `OPENAI_API_KEY` | **Only** OpenAI Agents SDK trace export to [OpenAI Traces](https://platform.openai.com/logs/trace); also **fallback** LLM key if `OPENROUTER_API_KEY` is unset |
| `LLM_MODEL` | OpenRouter model id (e.g. `openai/gpt-4.1-mini`); alias `AGENT_MODEL` |
| `EMBEDDING_MODEL` | OpenRouter embedding id (e.g. `openai/text-embedding-3-small`) |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key (frontend; also set in repo-root `.env` loaded by Next) |
| `CLERK_SECRET_KEY` | Clerk secret (frontend middleware / server) |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | e.g. `/sign-in` |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | e.g. `/sign-up` |
| `NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL` | e.g. `/Dashboard` |
| `NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL` | e.g. `/Dashboard` |
| `CLERK_JWKS_URL` | **Required** — JWKS URL for verifying Clerk JWTs on `/api/*` |
| `LANGFUSE_*` | Optional tracing |
| `CORS_ORIGINS` | Comma-separated origins for FastAPI |
| `NEXT_PUBLIC_API_URL` | Browser → FastAPI base URL |

Clerk is configured **only from environment variables** (repo-root `.env`; `frontend/next.config.ts` loads `../.env`). Sign-in/up components do not override URLs at runtime.

Chat runs through **`OpenAIChatCompletionsModel`** with base URL **`OPENROUTER_BASE_URL`** and key **`OPENROUTER_API_KEY` or `OPENAI_API_KEY`**. Trace uploads use **`OPENAI_API_KEY`** when passed via `RunConfig(tracing={"api_key": …})`.

## Project layout

```
capstone/
  backend/
    compliance_core/       # DB models, RAG, ComplianceToolService
    mcp_server/              # FastMCP stdio tools
    compliance_agents/       # Agents SDK orchestration + instructions
    routers/                 # FastAPI routers
    scripts/                 # seed_db, synthetic dataset, evaluate
    data/                    # synthetic_incidents.json (generated)
    main.py                  # FastAPI entrypoint
  frontend/                  # Next.js dashboard
  docker-compose.yml
  .env.example
```

## Production notes

- Replace seed regulation snippets with counsel-approved corpora and versioning.
- Tighten JWT validation (issuer/audience) for your Clerk instance.
- Run MCP subprocess with least-privilege DB credentials.
- Configure Langfuse project + sampling policies.

See **`USER_GUIDE.md`** for analyst-facing workflows.

# 🚀 Deployment Guide (AWS + Terraform + App Runner)

This project uses **Terraform** for infrastructure provisioning on AWS.  
Terraform remote state is stored in **S3**, with state locking handled via **DynamoDB**.

---

# 📦 One-Time Setup — Bootstrap Terraform Remote State

Before running Terraform normally, you must create:

- An **S3 bucket** → stores Terraform remote state
- A **DynamoDB table** → handles state locking

Run:

```bash
./scripts/bootstrap-terraform-state.sh
```

This script will:

- Create the S3 bucket (if it doesn't exist)
- Enable versioning
- Create the DynamoDB lock table
- Configure required backend settings

> ⚠️ This step is required **only once per AWS account/region**.

---

# 🏗 Step 1 — Initialize Terraform

After bootstrapping state:

```bash
terraform init
```

This will:

- Configure the remote S3 backend
- Connect to DynamoDB for locking
- Download required Terraform providers

---

# 🌍 Step 2 — Create the Environment (Phase 1)

Provision infrastructure:

```bash
terraform apply
```

Ensure the following variable is set:

```hcl
create_apprunner_service = false
```

This creates:

- Supporting infrastructure
- IAM roles
- Secrets


At this stage, **App Runner is NOT created yet**.

---

# 🔁 Step 3 — First GitHub Push (App Runner Disabled)

Commit and push with:

```hcl
create_apprunner_service = false
```

```bash
git add .
git commit -m "Initial infra setup without App Runner"
git push
```

This ensures:

- Core infrastructure is created
- No App Runner service attempts deployment yet
- You can validate IAM, networking, and database connectivity first

---

# 🚀 Step 4 — Enable App Runner (Phase 2)

Now update:

```hcl
create_apprunner_service = true
```

Commit and push again:

```bash
git add .
git commit -m "Enable App Runner deployment"
git push
```

Then apply Terraform:

```bash
terraform apply
```

This will:

- Create the AWS App Runner service
- Connect it to your GitHub repository
- Deploy the backend automatically
- Attach environment variables and IAM roles

---

# 🧠 Why Two-Phase Deployment?

This avoids:

- Premature service creation
- CI/CD race conditions
- Failed App Runner builds due to missing infrastructure
- Circular dependency issues

It ensures your:

1. Database  
2. Networking  
3. IAM  
4. Secrets  

are fully provisioned before service deployment.

---

# 🔐 Production Best Practices

- Enable S3 versioning (should already be done in bootstrap)
- Enable DynamoDB point-in-time recovery
- Use least-privilege IAM roles
- Store secrets in AWS Secrets Manager
- Enable CloudWatch logs for App Runner
- Restrict database security groups

---

# ✅ Full Deployment Flow Summary

```bash
# One time only
./scripts/bootstrap-terraform-state.sh

# Initialize terraform
terraform init

# Create environment (App Runner disabled)
terraform apply

# Push with create_apprunner_service = false

# Update variable to true
# Push again

terraform apply
```