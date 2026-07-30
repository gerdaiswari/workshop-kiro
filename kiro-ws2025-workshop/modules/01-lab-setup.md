# Module 01 – Build the Windows Server 2019 lab

## Deploy

```bash
./scripts/00_deploy.sh \
  --region ap-southeast-1 \
  --profile default \
  --stack-name kiro-ws2025-lab
```

The script:

1. Creates or reuses a region-unique S3 artifact bucket.
2. Downloads XAMPP on the operator workstation when it is not already cached, validates its pinned SHA-256, and uploads it to the private bucket.
3. Packages bootstrap scripts and application source.
4. Deploys `infra/lab.yaml`.
5. Waits for APP01 and DATA01 bootstrap signals.
6. Writes stack state and outputs under `results/deployment/`.

Bootstrap can take 30–90 minutes because DATA01 installs three database engines and SQL Server Express requires a two-stage extraction before setup. CloudFormation fails rather than declaring success when a bootstrap script fails.

## Inspect outputs

```bash
aws cloudformation describe-stacks \
  --stack-name kiro-ws2025-lab \
  --query 'Stacks[0].Outputs' \
  --region ap-southeast-1 --profile default
```

Open `http://<LoadBalancerDns>/` and test:

```text
/health.html
/spring/actuator/health
/spring/api/info
/next/
/next/api/health
/data/api/status.php
```

## Verify SSM

```bash
aws ssm describe-instance-information \
  --filters Key=tag:Project,Values=kiro-ws2025-workshop \
  --region ap-southeast-1 --profile default
```

Both source instances must be `Online`. There is no RDP ingress; use Session Manager only if troubleshooting is required.

## Understand the applications

Ask Kiro:

```text
Inspect apps/, bootstrap/, and infra/lab.yaml. Explain how each workload is built, which Windows service owns it, which endpoint proves behavior, and which external downloads make bootstrap non-hermetic. Do not make changes.
```

**Checkpoint:** stack complete, both instances SSM Online, and all seven URL routes respond.

## If deployment rolls back

Extract the first failed resource and read durable bootstrap logs:

```bash
aws cloudformation describe-stack-events --stack-name kiro-ws2025-lab \
  --query "StackEvents[?contains(ResourceStatus, 'FAILED')].[Timestamp,LogicalResourceId,ResourceStatusReason]" \
  --output table --region ap-southeast-1 --profile default

aws s3 ls \
  s3://<artifact-bucket>/logs/kiro-ws2025-lab/ \
  --recursive --region ap-southeast-1 --profile default
```

A stack in `ROLLBACK_COMPLETE` cannot be updated. After reviewing the resource IDs, delete only the failed stack metadata/resources and wait before retrying:

```bash
aws cloudformation delete-stack --stack-name kiro-ws2025-lab \
  --region ap-southeast-1 --profile default
aws cloudformation wait stack-delete-complete --stack-name kiro-ws2025-lab \
  --region ap-southeast-1 --profile default
```

The artifact bucket is intentionally outside the stack, so payloads and bootstrap diagnostics survive rollback.
