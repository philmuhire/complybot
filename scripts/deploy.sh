#!/usr/bin/env bash
# Capstone deploy: Terraform (S3, CloudFront, ECR, App Runner) + push API image + static frontend to S3.
#
# Usage: ./scripts/deploy.sh <workspace> [project_name]
#   workspace     Terraform workspace: dev | test | prod (default dev)
#   project_name  Only used if terraform.tfvars is missing (must match ECR name / resources)
#
# Prereqs: AWS CLI, Terraform >= 1.5, Docker, remote state (see scripts/bootstrap-terraform-state.sh)
#
# Env (optional):
#   SKIP_TERRAFORM=1  — only build + push (skip terraform init/apply)
#   SKIP_DOCKER_PUSH=1  — no Docker; use for local work, then `git push main` and let GitHub Actions
#     build the linux/amd64 image on ubuntu-latest and push to ECR
#   SKIP_FRONTEND=1
#   CI=1              — use npm ci in frontend
#   DEFAULT_AWS_REGION / AWS_REGION
#
# With terraform.tfvars present, project_name and environment in that file are authoritative;
#   workspace in $1 must still match the environment you intend (e.g. prod).

set -euo pipefail

log() { printf '\n[deploy] %s\n' "$*"; }
err() { printf '\n[deploy] ERROR: %s\n' "$*" >&2; }

ENVIRONMENT="${1:-dev}"
# Used for S3 state bucket name. If unset, we try terraform.tfvars project_name.
OVERRIDE_PROJECT_NAME="${2:-}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform"
AWS_REGION="${DEFAULT_AWS_REGION:-${AWS_REGION:-us-east-1}}"
export AWS_REGION

if ! command -v terraform &>/dev/null; then
  err "terraform not found"
  exit 1
fi
if ! command -v aws &>/dev/null; then
  err "aws CLI not found"
  exit 1
fi

AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
log "Account ${AWS_ACCOUNT_ID}  Region ${AWS_REGION}  Workspace ${ENVIRONMENT}"

cd "$TF_DIR"

tfvars_project() {
  [ -f terraform.tfvars ] || return
  local line
  line=$(grep -E '^\s*project_name\s*=' terraform.tfvars 2>/dev/null | head -1) || return
  if echo "$line" | grep -q '"'; then
    echo "$line" | sed 's/^[^\"]*"\([^\"]*\)".*/\1/'
  elif echo "$line" | grep -q "'"; then
    echo "$line" | sed "s/^[^']*'\([^']*\)'.*/\1/"
  else
    echo "$line" | sed 's/[^=]*=[[:space:]]*\([[:alnum:]_-]*\).*/\1/'
  fi
}

STATE_PROJECT="${OVERRIDE_PROJECT_NAME:-${TF_STATE_PROJECT_NAME:-${TF_VAR_project_name:-}}}"
[ -n "$STATE_PROJECT" ] || STATE_PROJECT="$(tfvars_project 2>/dev/null || true)"
[ -n "$STATE_PROJECT" ] || STATE_PROJECT="capstone"

if [ -f terraform.tfvars ]; then
  log "Using terraform.tfvars (state bucket prefix: ${STATE_PROJECT})"
else
  log "No terraform.tfvars; using -var project_name=${STATE_PROJECT} environment=${ENVIRONMENT} (or set TF_VAR_* in env for local/CI only)"
fi

if [ -n "${CI:-}" ] && [ ! -f terraform.tfvars ] && [ "${SKIP_TERRAFORM:-0}" != "1" ]; then
  err "In CI, the workflow should write TERRAFORM_TFVARS to infra/terraform/terraform.tfvars, or you commit a tfvars there. See .github/workflows/deploy.yml"
  exit 1
fi

# If a tfvars file exists, drop TF_VAR_* for the same keys so empty CI env does not override the file
if [ -f terraform.tfvars ]; then
  for _k in openai_api_key clerk_issuer clerk_jwks_url clerk_secret_key \
    langfuse_public_key langfuse_secret_key openrouter_api_key supabase_database_url \
    github_org github_repo; do
    unset "TF_VAR_${_k}" 2>/dev/null || true
  done
  unset _k
fi

log "terraform init (remote backend)…"
terraform init -input=false \
  -backend-config="bucket=${STATE_PROJECT}-terraform-state-${AWS_ACCOUNT_ID}" \
  -backend-config="key=${ENVIRONMENT}/terraform.tfstate" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${STATE_PROJECT}-terraform-locks" \
  -backend-config="encrypt=true"

if terraform workspace list 2>/dev/null | sed 's/^[ *]*//' | grep -qx "$ENVIRONMENT"; then
  terraform workspace select "$ENVIRONMENT"
else
  terraform workspace new "$ENVIRONMENT"
fi

if [ "${SKIP_TERRAFORM:-0}" = "1" ]; then
  log "SKIP_TERRAFORM=1 — no apply; using existing state for outputs"
else
  # One arg array: bash 3.2 + set -u errors on empty "${a[@]}", so we only += (never empty [@])
  TERRAFORM_APPLY=(-input=false -auto-approve)
  if [ -f terraform.tfvars ]; then
    TERRAFORM_APPLY+=(-var-file=terraform.tfvars)
    if [ "$ENVIRONMENT" = "prod" ] && [ -f prod.tfvars ]; then
      TERRAFORM_APPLY+=(-var-file=prod.tfvars)
      log "Including prod.tfvars"
    fi
    TERRAFORM_APPLY+=(-var="environment=${ENVIRONMENT}")
  else
    TERRAFORM_APPLY+=(
      -var="project_name=${STATE_PROJECT}"
      -var="environment=${ENVIRONMENT}"
    )
    if [ "$ENVIRONMENT" = "prod" ] && [ -f prod.tfvars ]; then
      TERRAFORM_APPLY+=(-var-file=prod.tfvars)
      log "Including prod.tfvars"
    fi
  fi
  terraform apply "${TERRAFORM_APPLY[@]}"
fi

API_URL="$(terraform output -raw app_runner_service_url 2>/dev/null || terraform output -raw api_gateway_url)"
ECR_URL="$(terraform output -raw ecr_repository_url)"
FRONTEND_BUCKET="$(terraform output -raw s3_frontend_bucket 2>/dev/null || terraform output -raw frontend_bucket_name)"
CLOUDFRONT_ID="$(terraform output -raw cloudfront_distribution_id)"
CLOUDFRONT_URL="$(terraform output -raw cloudfront_url 2>/dev/null || terraform output -raw frontend_url)"
IMAGE_URI="${ECR_URL}:latest"

log "API URL:           ${API_URL:-}"
log "ECR image:         ${IMAGE_URI}"
log "S3 bucket:         ${FRONTEND_BUCKET}"
log "CloudFront:        ${CLOUDFRONT_URL}"
log "Distribution id:  ${CLOUDFRONT_ID}"

# No App Runner yet (create_apprunner_service=false): still push image; skip static build without API URL
if [ -z "${API_URL:-}" ] && [ "${SKIP_FRONTEND:-0}" != "1" ]; then
  log "No app_runner URL in state (bootstrap: set create_apprunner_service=true after ECR has an image, then apply). Skipping static frontend for this run."
  SKIP_FRONTEND=1
fi

# --- API image ---
if [ "${SKIP_DOCKER_PUSH:-0}" != "1" ]; then
  if ! command -v docker &>/dev/null; then
    err "docker not found; set SKIP_DOCKER_PUSH=1 to skip"
    exit 1
  fi
  log "Logging in to ECR…"
  aws ecr get-login-password --region "$AWS_REGION" \
    | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

  # linux/amd64 (what App Runner runs). On arm64 (Apple Silicon), use Buildx + --push
  # (QEMU is bundled with Docker Desktop; first amd64 build may be slow).
  if docker buildx version &>/dev/null; then
    log "buildx: building linux/amd64 and pushing to ECR (OK on M1/M2/M3)…"
    docker buildx build --platform linux/amd64 --provenance=false \
      -f "$ROOT/backend/Dockerfile" -t "$IMAGE_URI" --push "$ROOT"
  else
    log "docker build --platform linux/amd64 (install Docker Desktop with buildx for best arm64 support)…"
    docker build --platform linux/amd64 -f "$ROOT/backend/Dockerfile" -t "$IMAGE_URI" "$ROOT"
    docker push "$IMAGE_URI"
  fi
  log "Pushed ${IMAGE_URI} (App Runner auto-deploys when this tag updates)"
else
  log "SKIP_DOCKER_PUSH=1 — no Docker build/push"
fi

# --- Static frontend → S3 + invalidation ---
if [ "${SKIP_FRONTEND:-0}" != "1" ]; then
  log "Preparing frontend .env.production…"
  cd "$ROOT/frontend"
  {
    echo "NEXT_PUBLIC_API_URL=${API_URL}"
    [ -n "${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY:-}" ] && echo "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}"
    [ -n "${NEXT_PUBLIC_CLERK_SIGN_IN_URL:-}" ] && echo "NEXT_PUBLIC_CLERK_SIGN_IN_URL=${NEXT_PUBLIC_CLERK_SIGN_IN_URL}"
    [ -n "${NEXT_PUBLIC_CLERK_SIGN_UP_URL:-}" ] && echo "NEXT_PUBLIC_CLERK_SIGN_UP_URL=${NEXT_PUBLIC_CLERK_SIGN_UP_URL}"
    [ -n "${NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL:-}" ] && echo "NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=${NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL}"
  } > .env.production

  if [ -n "${CI:-}" ] && [ -f package-lock.json ]; then
    log "npm ci (CI)…"
    npm ci
  else
    log "npm install…"
    npm install
  fi

  log "Building static export (STATIC_EXPORT=true)…"
  STATIC_EXPORT=true npm run build:static 2>/dev/null || STATIC_EXPORT=true npm run build

  if [ ! -d out ]; then
    err "No out/ after build. Ensure next.config has output: export when STATIC_EXPORT=true"
    exit 1
  fi

  log "aws s3 sync to s3://${FRONTEND_BUCKET}…"
  aws s3 sync ./out "s3://${FRONTEND_BUCKET}/" --delete

  log "CloudFront invalidation /* …"
  aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_ID" \
    --paths "/*" --output text --query 'Invalidation.Id' --no-cli-pager
else
  log "SKIP_FRONTEND=1 — no Next build or S3 sync"
fi

log "Done"
printf '  %s %s\n' "Site:" "$CLOUDFRONT_URL"
printf '  %s %s\n' "API: " "$API_URL"
echo ""
