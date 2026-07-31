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

## 2. Start APP01 in terminal 1

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

Type `APP01` when prompted. Keep this terminal open: the script polls until the automation reaches a terminal state and continuously updates `results/upgrades/APP01.json`.

The expected runbook inputs include:

```text
IamInstanceProfile=<stack output>
InstanceId=<APP01 source ID>
SubnetId=<public subnet>
TargetWindowsVersion=2025
KeepPreUpgradeImageBackUp=True
RebootInstanceBeforeTakingImage=False
```

## 3. Start DATA01 in terminal 2

Open a **separate terminal** in the repository root. Start DATA01 only after its baseline and native-backup evidence pass. It does not need to wait for APP01 to finish because the two executions target different source instances and write separate evidence files.

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

Type `DATA01` when prompted and keep this terminal open. Running both automations concurrently consumes more temporary EC2/EBS capacity, so confirm the workshop account quota and facilitator instruction before starting.

### Continue learning while the upgrades run

After both terminals show an automation execution ID/status, take the scheduled break and then continue in a third terminal:

1. [Module 09](09-mcp-integration.md) — add AWS Knowledge MCP.
2. [Module 10](10-skills-and-reuse.md) — create a reusable skill.
3. [Module 10B](10b-agents-and-subagents.md) — create specialized agents and use subagents.

Periodically inspect both upgrade terminals. Do **not** continue to Module 07 until both scripts report `Success` and both evidence files contain an `upgraded_ami_id`.

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
