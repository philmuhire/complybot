#!/usr/bin/env bash
# One-time: create the S3 bucket and DynamoDB table for Terraform remote state
# (must run with credentials that can create S3 and Dynamo in the account)
#
# Usage: ./scripts/bootstrap-terraform-state.sh <project_name> <aws_region> [state_account_id]
# Example: ./scripts/bootstrap-terraform-state.sh compliance us-east-1
#
# Bucket name matches scripts/deploy.sh:  ${project_name}-terraform-state-${account_id}
# Table name:                          ${project_name}-terraform-locks
set -euo pipefail

P="${1:-}"
R="${2:-us-east-1}"
ACC="${3:-$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")}"
if [ -z "$P" ] || [ -z "$ACC" ]; then
  echo "Usage: $0 <project_name> <aws_region> [aws_account_id]"
  exit 1
fi

BUCKET="${P}-terraform-state-${ACC}"
LOCK="${P}-terraform-locks"

if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "Bucket exists: s3://$BUCKET"
else
  if [ "$R" = "us-east-1" ] || [ "$R" = "us-west-1" ] || [ "$R" = "us-west-2" ]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$R" \
      --object-ownership BucketOwnerEnforced
  else
    aws s3api create-bucket --bucket "$BUCKET" --region "$R" \
      --create-bucket-configuration "LocationConstraint=$R" --object-ownership BucketOwnerEnforced
  fi
  aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
  aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
  echo "Created: s3://$BUCKET"
fi

if aws dynamodb describe-table --table-name "$LOCK" --region "$R" &>/dev/null; then
  echo "DynamoDB table exists: $LOCK"
else
  aws dynamodb create-table --table-name "$LOCK" --billing-mode PAY_PER_REQUEST --region "$R" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH
  echo "Created DynamoDB table: $LOCK"
fi
echo "Done. Next: use scripts/deploy.sh or terraform init with the same bucket/table names as in deploy.sh"
