variable "project_name" {
  type        = string
  description = "Short name prefix for AWS resources."
  default     = "capstone"
}

variable "environment" {
  type        = string
  description = "Logical environment (dev | test | prod). Use Terraform workspaces in deploy.sh."
  default     = "dev"
}

variable "aws_region" {
  type        = string
  description = "Primary AWS region."
  default     = "us-east-1"
}

variable "github_org" {
  type        = string
  description = "GitHub org or user (OIDC subject)."
}

variable "github_repo" {
  type        = string
  description = "Repository name (OIDC subject)."
}

variable "github_branch" {
  type        = string
  description = "Branch allowed for the GitHub Actions deploy role (OIDC)"
  default     = "main"
}

variable "create_github_oidc_provider" {
  type        = bool
  description = <<-EOT
    Set to false if this account already has the GitHub OIDC provider.
    In that case set github_oidc_provider_arn.
  EOT
  default     = true
}

variable "github_oidc_thumbprints" {
  type = list(string)
  default = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd",
  ]
}

variable "github_oidc_provider_arn" {
  type        = string
  description = "Existing GitHub OIDC provider ARN if create_github_oidc_provider is false"
  default     = ""
}

# false = create ECR + the rest, skip App Runner until a :latest image exists (e.g. from GitHub Actions). Then set true and apply.
variable "create_apprunner_service" {
  type        = bool
  default     = true
  description = "Set false for the first apply so the first 'push to main' can build/push the image; then set true, apply, and the service can start."
}

variable "apprunner_cpu" {
  type    = string
  default = "1024"
}

variable "apprunner_memory" {
  type    = string
  default = "2048"
}

variable "cloudfront_price_class" {
  type    = string
  default = "PriceClass_100"
}

# — App Runner container env (same idea as: OPENROUTER_API_KEY = var.openrouter_api_key in the service block) —
# In GitHub Actions, paste the full file into secret TERRAFORM_TFVARS; the workflow writes infra/terraform/terraform.tfvars before deploy.

variable "clerk_issuer" {
  type        = string
  description = "CLERK_ISSUER"
  sensitive   = true
}
variable "clerk_jwks_url" {
  type        = string
  description = "CLERK_JWKS_URL"
  sensitive   = true
}
variable "clerk_secret_key" {
  type        = string
  description = "CLERK_SECRET_KEY"
  sensitive   = true
}
variable "embedding_model" {
  type    = string
  default = "openai/text-embedding-3-small"
}
variable "langfuse_base_url" {
  type    = string
  default = "https://cloud.langfuse.com"
}
variable "langfuse_host" {
  type    = string
  default = "https://cloud.langfuse.com"
}
variable "langfuse_public_key" {
  type      = string
  sensitive = true
}
variable "langfuse_secret_key" {
  type      = string
  sensitive = true
}
variable "llm_model" {
  type    = string
  default = "openai/gpt-4.1-mini"
}
variable "openai_agents_disable_tracing" {
  type    = string
  default = "false"
}
variable "openai_api_key" {
  type      = string
  sensitive = true
}
variable "openrouter_api_key" {
  type      = string
  sensitive = true
}
variable "openrouter_base_url" {
  type    = string
  default = "https://openrouter.ai/api/v1"
}
variable "supabase_database_url" {
  type      = string
  sensitive = true
}

variable "apprunner_auto_deploy" {
  type        = bool
  description = "Set false to only deploy new revisions when you update the service in Terraform; true to deploy on ECR :latest push."
  default     = true
}

variable "apprunner_instance_role_arn" {
  type        = string
  description = "Optional. IAM role for the running service (AWS API access from the container). Empty = not set."
  default     = ""
}

# Optional extra key/value pairs (rare) merged last (does not override CORS_ORIGINS).
variable "apprunner_environment_extras" {
  type        = map(string)
  default     = {}
  sensitive   = true
  description = "Optional additional runtime_environment_variables merged after explicit vars and CORS_ORIGINS."
}

variable "additional_cors_origins" {
  type        = string
  description = "Optional extra CORS origins (comma-separated) in addition to the CloudFront URL"
  default     = ""
}
