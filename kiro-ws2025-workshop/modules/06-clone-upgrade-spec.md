# Module 06 – Clone-upgrade to Windows Server 2025

## Learning objective
Review the high-impact change in Kiro Spec mode, then start the AWS-owned clone-upgrade automation separately for APP01 and DATA01 with explicit confirmation.

## 1. Review the change in Spec mode

Start Spec mode with the agent you created:

```text
kiro-cli chat --v3 --mode spec --agent my-windows-upgrade
```

At the Kiro prompt:

```text
Review the existing clone-upgrade Spec under .kiro/specs/clone-upgrade/.
For APP01 and DATA01, state the source instance ID, subnet, instance profile,
target Windows version, runbook parameters, expected duration and cost,
backup prerequisites, rollback artifacts, and stop conditions.
Do not call AWS and do not edit files.
```

Do not run upgrade tasks unattended or with `--trust-all-tools`. The deterministic script below requires typed confirmation for each server.

## 2. Upgrade APP01

**Windows PowerShell:**

```powershell
py -3 scripts\04_start_upgrade.py `
  --server APP01 `
  --region us-east-1 `
  --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/04_start_upgrade.py \
  --server APP01 \
  --region us-east-1 \
  --stack-name kiro-ws2025-lab
```

Type `APP01` when prompted. The script polls to a terminal status and saves `results/upgrades/APP01.json`.

The expected runbook inputs include:

```text
IamInstanceProfile=<stack output>
InstanceId=<APP01 source ID>
SubnetId=<public subnet>
TargetWindowsVersion=2025
KeepPreUpgradeImageBackUp=True
RebootInstanceBeforeTakingImage=False
```

## 3. Upgrade DATA01 separately

Continue only after APP01 completes and DATA01 native backup evidence passes.

**Windows PowerShell:**

```powershell
py -3 scripts\04_start_upgrade.py `
  --server DATA01 `
  --region us-east-1 `
  --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/04_start_upgrade.py \
  --server DATA01 \
  --region us-east-1 \
  --stack-name kiro-ws2025-lab
```

## 4. Inspect an execution

The AWS CLI command is identical on all platforms when written on one line:

```text
aws ssm get-automation-execution --automation-execution-id <execution-id> --region us-east-1
```

A failure is evidence, not permission to modify the source blindly. Start a normal session with your agent and ask it to analyze the failed step, logs, prerequisites, and remediation options without taking action:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

**Checkpoint:** successful execution evidence contains an upgraded AMI ID for each server, and both source instances remain healthy on Windows Server 2019.
