# Module 00 – Prerequisites and assumptions

## Learning objective
Establish identity, tooling, quota, cost, and the boundaries that make this a safe lab rather than a production recipe.

## Local preflight

```bash
kiro-cli --version
aws --version
python3 --version
git --version
aws sts get-caller-identity --profile default
python3 tests/static/validate_repo.py
```

Use Kiro CLI 3.x for standalone hooks, permissions, and `/spec`. If a feature is missing, update Kiro rather than silently skipping its control.

## AWS access

The deployer needs CloudFormation, EC2, IAM, S3, Elastic Load Balancing v2, and SSM permissions. The principal starting an upgrade also needs the permissions required by `AWSEC2-CloneInstanceAndUpgradeWindows` to create images, run/terminate its temporary instance, manage temporary volumes, pass the instance profile, and tag resources. Use a dedicated sandbox account where possible.

## Confirm regional interfaces

```bash
aws ssm describe-document \
  --name AWSEC2-CloneInstanceAndUpgradeWindows \
  --region ap-southeast-1 --profile default

aws ssm get-parameter \
  --name /aws/service/ami-windows-latest/Windows_Server-2019-English-Full-Base \
  --region ap-southeast-1 --profile default
```

## Cost and time

Budget USD 15–35 for a complete run, depending on region and how long resources remain. The two AWS upgrade executions may each take about two hours. Do not schedule a live workshop that depends on both finishing synchronously; instructors can run the upgrade ahead of time and preserve output AMI IDs.

## Non-goals

- No production data, domain joins, certificates, or external integrations.
- No proof of third-party vendor certification.
- No database production cutover.
- No guarantee that the same scripts cover all 40 real servers.

**Checkpoint:** tools work, AWS identity is correct, runbook and AMI parameter exist, and the participant accepts cost/time.
