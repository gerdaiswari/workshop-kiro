#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGION=""
PROFILE="default"
STACK_NAME="kiro-ws2025-lab"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --region) REGION="$2"; shift 2 ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --stack-name) STACK_NAME="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$REGION" ]]; then
  echo "Usage: $0 --region REGION [--profile PROFILE] [--stack-name NAME]" >&2
  exit 2
fi

for command in aws python3; do
  command -v "$command" >/dev/null || { echo "$command is required" >&2; exit 1; }
done

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text --region "$REGION" --profile "$PROFILE")"
SAFE_STACK="$(printf '%s' "$STACK_NAME" | tr '[:upper:]_' '[:lower:]-' | tr -cd 'a-z0-9-')"
BUCKET="kiro-ws2025-${ACCOUNT_ID}-${REGION}-${SAFE_STACK}"
ARTIFACT_KEY="payload/workshop-payload.zip"
ZIP="$ROOT/results/deployment/workshop-payload.zip"
mkdir -p "$ROOT/results/deployment"

python3 "$ROOT/scripts/lib/package_payload.py" --root "$ROOT" --output "$ZIP"

if ! aws s3api head-bucket --bucket "$BUCKET" --region "$REGION" --profile "$PROFILE" 2>/dev/null; then
  if [[ "$REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" --profile "$PROFILE" >/dev/null
  else
    aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration "LocationConstraint=$REGION" --region "$REGION" --profile "$PROFILE" >/dev/null
  fi
  aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
    --region "$REGION" --profile "$PROFILE"
  aws s3api put-bucket-encryption --bucket "$BUCKET" \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
    --region "$REGION" --profile "$PROFILE"
fi

aws s3 cp "$ZIP" "s3://$BUCKET/$ARTIFACT_KEY" --region "$REGION" --profile "$PROFILE" --only-show-errors

aws cloudformation deploy \
  --template-file "$ROOT/infra/lab.yaml" \
  --stack-name "$STACK_NAME" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides "ArtifactBucketName=$BUCKET" "ArtifactKey=$ARTIFACT_KEY" \
  --region "$REGION" --profile "$PROFILE" \
  --no-fail-on-empty-changeset

aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
  --region "$REGION" --profile "$PROFILE" --output json \
  > "$ROOT/results/deployment/stack.json"

python3 - "$ROOT/results/deployment/state.json" "$STACK_NAME" "$REGION" "$PROFILE" "$BUCKET" <<'PY'
import json, sys
from datetime import datetime, timezone
path, stack, region, profile, bucket = sys.argv[1:]
with open(path, 'w', encoding='utf-8') as handle:
    json.dump({
        'stack_name': stack, 'region': region, 'profile': profile,
        'artifact_bucket': bucket, 'created_at': datetime.now(timezone.utc).isoformat()
    }, handle, indent=2)
    handle.write('\n')
PY

DNS="$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDns'].OutputValue | [0]" --output text --region "$REGION" --profile "$PROFILE")"
echo "Lab ready. ALB: http://$DNS/"
echo "State: $ROOT/results/deployment/state.json"
