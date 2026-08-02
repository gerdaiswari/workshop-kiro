#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGION=""
PROFILE=""
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

AWS_CONTEXT=(--region "$REGION")
PROFILE_DISPLAY="environment"
if [[ -n "$PROFILE" ]]; then
  AWS_CONTEXT+=(--profile "$PROFILE")
  PROFILE_DISPLAY="$PROFILE"
fi

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text "${AWS_CONTEXT[@]}")"
SAFE_STACK="$(printf '%s' "$STACK_NAME" | tr '[:upper:]_' '[:lower:]-' | tr -cd 'a-z0-9-')"
BUCKET="kiro-ws2025-${ACCOUNT_ID}-${REGION}-${SAFE_STACK}"
ARTIFACT_KEY="payload/workshop-payload.zip"
XAMPP_KEY="dependencies/xampp-windows-x64-8.2.12-0-VS16-installer.exe"
XAMPP_SIZE="157583456"
XAMPP_SHA256="12e818ce5aec79fe646606df3a80b35da865ec0213646ad7c92044dcfcec7535"
XAMPP_FILE="$ROOT/results/deployment/xampp-windows-x64-8.2.12-0-VS16-installer.exe"
ZIP="$ROOT/results/deployment/workshop-payload.zip"
mkdir -p "$ROOT/results/deployment"

EXISTING_STATUS="$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
  --query 'Stacks[0].StackStatus' --output text "${AWS_CONTEXT[@]}" 2>/dev/null || true)"
if [[ "$EXISTING_STATUS" == "ROLLBACK_COMPLETE" ]]; then
  cat >&2 <<EOF
Stack $STACK_NAME is ROLLBACK_COMPLETE and cannot be updated.
Review the failed events and S3 bootstrap logs, then delete only this rolled-back stack before retrying.
Use the same environment credentials or optional named profile used for deployment.
EOF
  exit 3
fi

python3 "$ROOT/scripts/lib/package_payload.py" --root "$ROOT" --output "$ZIP"

if ! aws s3api head-bucket --bucket "$BUCKET" "${AWS_CONTEXT[@]}" 2>/dev/null; then
  if [[ "$REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$BUCKET" "${AWS_CONTEXT[@]}" >/dev/null
  else
    aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration "LocationConstraint=$REGION" "${AWS_CONTEXT[@]}" >/dev/null
  fi
  aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
    "${AWS_CONTEXT[@]}"
  aws s3api put-bucket-encryption --bucket "$BUCKET" \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
    "${AWS_CONTEXT[@]}"
fi

aws s3 rm "s3://$BUCKET/logs/$STACK_NAME/" --recursive --only-show-errors \
  "${AWS_CONTEXT[@]}" || echo "Warning: could not clear prior bootstrap logs" >&2

REMOTE_XAMPP="$(aws s3api head-object --bucket "$BUCKET" --key "$XAMPP_KEY" \
  --query '[ContentLength,Metadata.sha256]' --output text \
  "${AWS_CONTEXT[@]}" 2>/dev/null || true)"
read -r REMOTE_XAMPP_SIZE REMOTE_XAMPP_SHA256 <<< "$REMOTE_XAMPP"
if [[ "$REMOTE_XAMPP_SIZE" != "$XAMPP_SIZE" || "$REMOTE_XAMPP_SHA256" != "$XAMPP_SHA256" ]]; then
  python3 "$ROOT/scripts/lib/cache_dependency.py" \
    --url 'https://netix.dl.sourceforge.net/project/xampp/XAMPP%20Windows/8.2.12/xampp-windows-x64-8.2.12-0-VS16-installer.exe' \
    --url 'https://master.dl.sourceforge.net/project/xampp/XAMPP%20Windows/8.2.12/xampp-windows-x64-8.2.12-0-VS16-installer.exe' \
    --url 'https://phoenixnap.dl.sourceforge.net/project/xampp/XAMPP%20Windows/8.2.12/xampp-windows-x64-8.2.12-0-VS16-installer.exe' \
    --url 'https://onboardcloud.dl.sourceforge.net/project/xampp/XAMPP%20Windows/8.2.12/xampp-windows-x64-8.2.12-0-VS16-installer.exe' \
    --output "$XAMPP_FILE" --minimum-bytes 150000000 --magic MZ --sha256 "$XAMPP_SHA256"
  aws s3 cp "$XAMPP_FILE" "s3://$BUCKET/$XAMPP_KEY" \
    --metadata "sha256=$XAMPP_SHA256" "${AWS_CONTEXT[@]}" --only-show-errors
else
  echo "Reusing validated S3 dependency: s3://$BUCKET/$XAMPP_KEY"
fi

aws s3 cp "$ZIP" "s3://$BUCKET/$ARTIFACT_KEY" "${AWS_CONTEXT[@]}" --only-show-errors

if ! aws cloudformation deploy \
  --template-file "$ROOT/infra/lab.yaml" \
  --stack-name "$STACK_NAME" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides "ArtifactBucketName=$BUCKET" "ArtifactKey=$ARTIFACT_KEY" "XamppArtifactKey=$XAMPP_KEY" \
  "${AWS_CONTEXT[@]}" \
  --no-fail-on-empty-changeset; then
  echo "CloudFormation deployment failed. Failed resources:" >&2
  aws cloudformation describe-stack-events --stack-name "$STACK_NAME" \
    --query "StackEvents[?contains(ResourceStatus, 'FAILED')].[Timestamp,LogicalResourceId,ResourceStatusReason]" \
    --output table "${AWS_CONTEXT[@]}" >&2 || true
  echo "Durable bootstrap logs, if uploaded:" >&2
  aws s3 ls "s3://$BUCKET/logs/$STACK_NAME/" --recursive "${AWS_CONTEXT[@]}" >&2 || true
  exit 1
fi

aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
  "${AWS_CONTEXT[@]}" --output json \
  > "$ROOT/results/deployment/stack.json"

python3 - "$ROOT/results/deployment/state.json" "$STACK_NAME" "$REGION" "$PROFILE_DISPLAY" "$BUCKET" <<'PY'
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

DNS="$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDns'].OutputValue | [0]" --output text "${AWS_CONTEXT[@]}")"
echo "Lab ready. ALB: http://$DNS/"
echo "State: $ROOT/results/deployment/state.json"
