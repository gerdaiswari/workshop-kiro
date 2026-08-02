# Module 06 – Clone-upgrade to Windows Server 2025

## Learning objective
Review the high-impact change in Kiro Spec mode, then start the AWS-owned clone-upgrade automation separately for APP01 and DATA01 with explicit confirmation.

## Why this matters

This is the module where the actual Windows Server upgrade happens — but notice it doesn't upgrade your source servers in place. AWS's `AWSEC2-CloneInstanceAndUpgradeWindows` runbook takes an image of the source instance, upgrades a *temporary copy* of it to Windows Server 2025, and hands you back a new AMI — the original APP01 and DATA01 keep running untouched on Windows Server 2019 the whole time. You'll start this automation for both servers, each in its own terminal, because the runbook can take about two hours per server and you'll want to keep monitoring both while doing other things (Modules 09, 10, and 10B) during the wait.

> **Entry gate:** complete Module 05 first. `results/tests/baseline/summary.json` must show `passed: true`; before starting DATA01, `results/backups/summary.json` must also show `passed: true`. `04_start_upgrade.py` checks these files but does not create them — if you skipped Module 05, come back and run its baseline and backup steps first.

## Before opening the upgrade terminals

AWS credentials exported as environment variables apply only to the terminal where you exported them. Terminal 2 and Terminal 3 do **not** inherit credentials from Terminal 1. In every new terminal, first open the repository, export the latest temporary credentials from the workshop's **AWS account access** panel, and verify the AWS identity before running any workshop command.

**Linux/macOS Bash:**

```bash
cd /path/to/kiro-ws2025-workshop
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="<from lab>"
export AWS_SECRET_ACCESS_KEY="<from lab>"
export AWS_SESSION_TOKEN="<from lab>"
aws sts get-caller-identity --region us-east-1
```

**Windows PowerShell:**

```powershell
cd C:\path\to\kiro-ws2025-workshop
$env:AWS_DEFAULT_REGION="us-east-1"
$env:AWS_ACCESS_KEY_ID="<from lab>"
$env:AWS_SECRET_ACCESS_KEY="<from lab>"
$env:AWS_SESSION_TOKEN="<from lab>"
aws sts get-caller-identity --region us-east-1
```

Confirm that `get-caller-identity` shows the intended workshop/sandbox account. Do not continue if it fails or shows a production account. Never paste credential values into Kiro chat, workshop files, or Git.

If `04_start_upgrade.py` reports `ExpiredToken` while calling `cloudformation describe-stacks`, the script failed before the confirmation prompt and no upgrade was started. Export fresh credentials in that terminal, verify the identity again, and rerun the command. If the terminal has already displayed an Automation execution ID and status, the AWS automation is already running; do not start a duplicate execution. Export fresh credentials and inspect the existing execution as described in step 4.

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

Do not run upgrade tasks unattended or with `--trust-all-tools` — this is exactly the kind of high-impact, billable, multi-hour AWS change that the safety rules require explicit approval for. The deterministic script below requires typed confirmation for each server, so you always consciously start each upgrade rather than it happening as a side effect of something else.

This shows that Kiro can help you prepare for a high-impact change — it reads your infrastructure code and evidence files, then summarizes exactly what will happen, what it will cost, how long it takes, and what the rollback looks like, so you make an informed decision before typing "yes".

### Runbook parameter spelling

The AWS documentation names the target input `TargetWindowsVersion`, but AWS-owned runbook version 46 in `us-east-1` exposes `TargetWindowVersion`. The script does not assume either spelling. Before approval, it reads the regional runbook schema, selects the spelling that actually exists, displays it with the document version, and pins that same version when starting Automation. If neither spelling exists, the script stops without creating an execution.

## 2. Start APP01 in terminal 1

In Terminal 1, complete the credential export and `get-caller-identity` verification above, then start APP01.

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

Type `APP01` when prompted — this typed confirmation is the actual approval gate; the script won't proceed without it. Keep this terminal open: the script polls until the automation reaches a terminal state (success or failure) and continuously updates `results/upgrades/APP01.json`, so you can watch progress without re-running anything.

The expected runbook inputs include the target-version spelling discovered from the pinned schema:

```text
IamInstanceProfile=<stack output>
InstanceId=<APP01 source ID>
SubnetId=<public subnet>
TargetWindowVersion=2025       # AWS runbook v46 runtime spelling
# or TargetWindowsVersion=2025 # documented spelling, if exposed by the region
KeepPreUpgradeImageBackUp=True
RebootInstanceBeforeTakingImage=False
```

## 3. Start DATA01 in terminal 2

Open a **separate terminal** in the repository root — this is the second of the two concurrent upgrade terminals mentioned above. Export the latest AWS credentials in Terminal 2 and run `aws sts get-caller-identity` again; credentials from Terminal 1 are not available here. Start DATA01 only after the identity is correct and its baseline and native-backup evidence pass. It does not need to wait for APP01 to finish because the two executions target different source instances and write separate evidence files, so they run fully independently of each other.

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

After both terminals show an automation execution ID/status, take the scheduled break and then continue in a third terminal. Before using Terminal 3, open the repository there, export the latest AWS credentials again, and verify `aws sts get-caller-identity` as described above. Then continue with:

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

This shows that Kiro can help you troubleshoot automation failures — it reads execution logs and error details, correlates them with prerequisites and known issues, and proposes targeted fixes without touching the running system.

## Transfer to your environment

- **Lab exercise:** two named servers use recorded stack outputs and a known runbook parameter set; each execution requires typed confirmation and saves AMI/execution evidence.
- **Reusable pattern:** verify the installed automation document schema, prerequisites, backup state, rollback artifacts, quota/cost, stop conditions, and explicit approval before each change. Treat the operation as clone upgrade, not an in-place production upgrade.
- **Adapt before reuse:** discover instance profile, subnet, source/target support, edition/language, unsupported roles, free space, egress, KMS/IAM needs, concurrency, maintenance window, and state-consistency design. Never copy a parameter that the current runbook schema does not expose.

Adaptation prompt:

```text
Prepare a change proposal for one real server from measured evidence. Show the
exact current runbook schema, inputs, resource IDs, prerequisites, duration,
cost, rollback artifacts, stop conditions, and approval boundary. Do not execute.
```

**Checkpoint:** successful lab execution evidence contains an upgraded AMI ID for each server, and both source instances remain healthy on Windows Server 2019.
