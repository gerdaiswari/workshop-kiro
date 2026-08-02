# Module 11 – Cleanup

## Learning objective

Review and then execute the teardown of every billable resource this workshop created, verifying nothing is left running that would continue to incur charges.

## Why this matters

Everything built in Module 01 onward — EC2 instances, the ALB, EBS volumes, retained AMIs and snapshots from the clone-upgrades, and the CloudFormation stack itself — keeps costing money as long as it exists. This module tears it all down. Cleanup is destructive and intentionally separate from the upgrade flow: it's run as a standalone script with a plan/execute split and a typed confirmation, not as something Kiro decides to do on your behalf. Run it directly from your terminal, not from a broadly trusted Kiro session, so there's no ambiguity about what's being deleted and why.

## 1. Review the cleanup plan

The plan lists validation instances, retained AMIs and snapshots, the CloudFormation stack, and the artifact bucket recorded in workshop state — running with `-Plan`/`--plan` only *shows* you what would be deleted; it does not delete anything yet.

**Windows PowerShell:**

```powershell
.\scripts\08_cleanup.ps1 -Plan `
  -Region us-east-1 `
  -StackName kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
./scripts/08_cleanup.sh --plan \
  --region us-east-1 \
  --stack-name kiro-ws2025-lab
```

Review every resource ID in the output. Stop if it does not match this workshop — you want to be certain the plan only lists resources tagged for this lab, not something else in your account.

## 2. Execute after explicit approval

**Windows PowerShell:**

```powershell
.\scripts\08_cleanup.ps1 -Execute `
  -Region us-east-1 `
  -StackName kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
./scripts/08_cleanup.sh --execute \
  --region us-east-1 \
  --stack-name kiro-ws2025-lab
```

Type the stack name when prompted. The script acts only on resources recorded in the workshop's `results/` state and applies project/role tag safeguards where available, so it won't reach for resources outside what this workshop actually created. It then deletes the stack and artifact bucket.

Do not add `-Yes` on Windows or `--yes` on Linux/macOS during the guided workshop; the typed confirmation is intentional — it's the same safety pattern used for the clone-upgrade start in Module 06, giving you one last explicit chance to stop before deletion happens.

## 3. Verify deletion

This one-line AWS CLI command works on every workstation:

```text
aws cloudformation describe-stacks --stack-name kiro-ws2025-lab --region us-east-1
```

A `ValidationError` stating that the stack does not exist is expected — that's the confirmation that deletion succeeded, not a failure. Also inspect owned AMIs and snapshots carrying the project tag so no retained charges remain, since AMIs and snapshots created during clone-upgrades aren't always automatically deleted with the stack.

Preserve non-secret JSON or Markdown evidence if required. Do not retain generated database passwords or dumps.

**Checkpoint:** stack resources, validation instances, retained workshop AMIs/snapshots, ALB, EBS volumes, and artifact bucket are removed.
