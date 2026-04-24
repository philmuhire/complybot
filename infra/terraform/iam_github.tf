data "aws_iam_policy_document" "github_actions_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [local.github_oidc_provider_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    # GitHub: push/PR to a branch → sub = repo:ORG/REPO:ref:refs/heads/BRANCH
    # Jobs with environment: x → sub = repo:ORG/REPO:environment:NAME (not ref:...)
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/${var.github_branch}",
        "repo:${var.github_org}/${var.github_repo}:environment:*",
      ]
    }
  }
}

resource "aws_iam_role" "github_actions_deploy" {
  name               = "${var.project_name}-${var.environment}-gha-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume.json

  lifecycle {
    precondition {
      condition     = var.create_github_oidc_provider || length(var.github_oidc_provider_arn) > 0
      error_message = "When create_github_oidc_provider is false, set github_oidc_provider_arn"
    }
  }
}

data "aws_iam_policy_document" "github_actions_deploy" {
  statement {
    sid    = "ECRAuth"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "ECRPush"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
    ]
    resources = [aws_ecr_repository.backend.arn]
  }

  statement {
    sid    = "S3Frontend"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      aws_s3_bucket.frontend.arn,
      "${aws_s3_bucket.frontend.arn}/*",
    ]
  }

  statement {
    sid    = "CloudFrontInvalidate"
    effect = "Allow"
    actions = [
      "cloudfront:CreateInvalidation",
    ]
    resources = [aws_cloudfront_distribution.frontend.arn]
  }

  # Terraform S3 + DynamoDB backend (must match scripts/deploy.sh and bootstrap-terraform-state.sh)
  statement {
    sid       = "TerraformState"
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem", "dynamodb:DescribeTable"]
    resources = ["arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.project_name}-terraform-locks"]
  }

  statement {
    sid     = "TerraformS3"
    effect  = "Allow"
    actions = ["s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetBucketObjectLockConfiguration"]
    resources = [
      "arn:aws:s3:::${var.project_name}-terraform-state-${data.aws_caller_identity.current.account_id}",
      "arn:aws:s3:::${var.project_name}-terraform-state-${data.aws_caller_identity.current.account_id}/*",
    ]
  }

  # Create/update S3 resources for this module
  statement {
    sid       = "S3BucketCreate"
    effect    = "Allow"
    actions   = ["s3:CreateBucket"]
    resources = ["*"]
  }

  statement {
    sid       = "S3BucketConfig"
    effect    = "Allow"
    actions   = ["s3:DeleteBucket", "s3:PutBucketPolicy", "s3:DeleteBucketPolicy", "s3:PutPublicAccessBlock", "s3:PutBucketVersioning", "s3:GetBucketLocation", "s3:GetBucketPolicy"]
    resources = ["arn:aws:s3:::*"]
  }

  # After first bootstrap apply, GHA can mutate these services (still run initial apply with admin once if needed)
  statement {
    sid       = "TerraformServiceMutations"
    effect    = "Allow"
    actions   = ["apprunner:*"]
    resources = ["*"]
  }

  statement {
    sid       = "ECRMutations"
    effect    = "Allow"
    actions   = ["ecr:CreateRepository", "ecr:DeleteRepository"]
    resources = ["arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/*"]
  }

  statement {
    sid       = "CloudFrontAll"
    effect    = "Allow"
    actions   = ["cloudfront:*"]
    resources = ["*"]
  }

  # OIDC provider: Create* must be allowed on *; manage/delete on the provider ARN
  statement {
    sid       = "IAMOidcCreate"
    effect    = "Allow"
    actions   = ["iam:CreateOpenIDConnectProvider"]
    resources = ["*"]
  }

  statement {
    sid       = "IAMOidcReadDelete"
    effect    = "Allow"
    actions   = ["iam:DeleteOpenIDConnectProvider", "iam:GetOpenIDConnectProvider", "iam:ListOpenIDConnectProviders"]
    resources = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/*"]
  }

  statement {
    sid       = "IAMRolePolicies"
    effect    = "Allow"
    actions   = ["iam:GetRole", "iam:CreateRole", "iam:DeleteRole", "iam:UpdateRole", "iam:UpdateAssumeRolePolicy", "iam:PassRole", "iam:TagRole", "iam:CreatePolicy", "iam:AttachRolePolicy", "iam:DetachRolePolicy", "iam:DeleteRolePolicy", "iam:PutRolePolicy"]
    resources = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.project_name}-${var.environment}-*"]
  }
}

resource "aws_iam_role_policy" "github_actions_deploy" {
  name   = "deploy-policy"
  role   = aws_iam_role.github_actions_deploy.id
  policy = data.aws_iam_policy_document.github_actions_deploy.json
}
