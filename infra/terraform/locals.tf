locals {
  github_oidc_provider_arn = var.create_github_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : var.github_oidc_provider_arn

  cors_allowed = trimspace(var.additional_cors_origins) == "" ? "https://${aws_cloudfront_distribution.frontend.domain_name}" : "https://${aws_cloudfront_distribution.frontend.domain_name},${trimspace(var.additional_cors_origins)}"

  # Same pattern as: runtime_environment_variables = { OPENROUTER_API_KEY = var.openrouter_api_key, ... }
  apprunner_from_vars = {
    CLERK_ISSUER                  = var.clerk_issuer
    CLERK_JWKS_URL                = var.clerk_jwks_url
    CLERK_SECRET_KEY              = var.clerk_secret_key
    EMBEDDING_MODEL               = var.embedding_model
    LANGFUSE_BASE_URL             = var.langfuse_base_url
    LANGFUSE_HOST                 = var.langfuse_host
    LANGFUSE_PUBLIC_KEY           = var.langfuse_public_key
    LANGFUSE_SECRET_KEY           = var.langfuse_secret_key
    LLM_MODEL                     = var.llm_model
    OPENAI_AGENTS_DISABLE_TRACING = var.openai_agents_disable_tracing
    OPENAI_API_KEY                = var.openai_api_key
    OPENROUTER_API_KEY            = var.openrouter_api_key
    OPENROUTER_BASE_URL           = var.openrouter_base_url
    SUPABASE_DATABASE_URL         = var.supabase_database_url
  }

  apprunner_env = merge(
    local.apprunner_from_vars,
    var.apprunner_environment_extras,
    { CORS_ORIGINS = local.cors_allowed }
  )
}
