# Module 06 – Clone-upgrade to Windows Server 2025

## Review the change

```text
/spec clone-upgrade
```

Do not run this Spec unattended with broad tool trust. Before each server, Kiro should state the source ID, subnet, instance profile, target, runbook parameters, duration/cost, and rollback artifacts.

## Upgrade APP01

```bash
python3 scripts/04_start_upgrade.py \
  --server APP01 \
  --region ap-southeast-1 --profile default \
  --stack-name kiro-ws2025-lab
```

Type `APP01` at the confirmation prompt. The script polls to a terminal status and writes `results/upgrades/APP01.json`. It uses:

```text
IamInstanceProfile=<stack output>
InstanceId=<APP01 source ID>
SubnetId=<public subnet>
TargetWindowsVersion=2025
KeepPreUpgradeImageBackUp=True
RebootInstanceBeforeTakingImage=False
```

## Upgrade DATA01 separately

Only after APP01 completes and native backup evidence exists:

```bash
python3 scripts/04_start_upgrade.py \
  --server DATA01 \
  --region ap-southeast-1 --profile default \
  --stack-name kiro-ws2025-lab
```

## Inspect execution

```bash
aws ssm get-automation-execution \
  --automation-execution-id <execution-id> \
  --region ap-southeast-1 --profile default
```

Failure is a result, not a signal to modify source blindly. Ask Kiro to analyze the failed step, logs, runbook prerequisites, and remediation options.

**Checkpoint:** successful execution JSON includes an upgraded AMI ID for each server, and both source instances remain healthy on Windows Server 2019.
