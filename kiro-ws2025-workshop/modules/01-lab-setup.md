# Module 01 – Build the Windows Server 2019 lab

## Deploy

```bash
./scripts/00_deploy.sh \
  --region ap-southeast-1 \
  --profile default \
  --stack-name kiro-ws2025-lab
```

The script:

1. Creates a region-unique S3 artifact bucket.
2. Packages bootstrap scripts and application source.
3. Deploys `infra/lab.yaml`.
4. Waits for APP01 and DATA01 bootstrap signals.
5. Writes stack state and outputs under `results/deployment/`.

Bootstrap can take 30–75 minutes because DATA01 installs three database engines. CloudFormation fails rather than declaring success when a bootstrap script fails.

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
