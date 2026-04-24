resource "aws_apprunner_service" "backend" {
  count = var.create_apprunner_service ? 1 : 0

  service_name = "${var.project_name}-${var.environment}-api"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access.arn
    }

    # ECR :latest: true = new image push can deploy; false = only via Terraform
    auto_deployments_enabled = var.apprunner_auto_deploy

    image_repository {
      image_identifier      = "${aws_ecr_repository.backend.repository_url}:latest"
      image_repository_type = "ECR"
      image_configuration {
        port = "8080"
        # Like: OPENROUTER_API_KEY = var.openrouter_api_key — built in locals from var.* + CORS + optional extras
        runtime_environment_variables = local.apprunner_env
      }
    }
  }

  instance_configuration {
    cpu    = var.apprunner_cpu
    memory = var.apprunner_memory
    # Optional: same role pattern as the researcher service (e.g. AWS API from the app)
    instance_role_arn = var.apprunner_instance_role_arn != "" ? var.apprunner_instance_role_arn : null
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  depends_on = [
    aws_iam_role_policy_attachment.apprunner_ecr_access_managed,
    aws_cloudfront_distribution.frontend,
  ]
}
