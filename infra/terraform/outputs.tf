output "aws_account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.backend.repository_url
  description = "ECR image URL (no tag)."
}

output "github_actions_role_arn" {
  value       = aws_iam_role.github_actions_deploy.arn
  description = "GitHub Actions OIDC — set as AWS_ROLE_ARN in the repo or environment secrets"
}

output "app_runner_service_arn" {
  value       = var.create_apprunner_service ? aws_apprunner_service.backend[0].arn : ""
  description = "Empty when create_apprunner_service is false (bootstrap; image from CI first, then set true and apply)"
}

output "app_runner_service_url" {
  value       = var.create_apprunner_service ? "https://${aws_apprunner_service.backend[0].service_url}" : ""
  description = "HTTPS base URL of the API"
}

output "api_gateway_url" {
  value       = var.create_apprunner_service ? "https://${aws_apprunner_service.backend[0].service_url}" : ""
  description = "Same as app_runner_service_url (naming for scripts)"
}

output "s3_frontend_bucket" {
  value       = aws_s3_bucket.frontend.bucket
  description = "Static site bucket"
}

output "frontend_bucket_name" {
  value       = aws_s3_bucket.frontend.bucket
  description = "Alias of s3_frontend_bucket"
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.frontend.domain_name
  description = "abc123.cloudfront.net"
}

output "cloudfront_url" {
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
  description = "HTTPS site URL"
}

output "frontend_url" {
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
  description = "Alias of cloudfront_url"
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.frontend.id
  description = "Use for cache invalidation"
}

output "custom_domain_url" {
  value       = ""
  description = "Placeholder for optional custom domain"
}
