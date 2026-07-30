# Module 11 – Cleanup

Cleanup is destructive and intentionally separate from the upgrade flow. Run it directly from your terminal, not from a broadly trusted Kiro session.

## 1. Review the cleanup plan

The plan lists validation instances, retained AMIs and snapshots, the CloudFormation stack, and the artifact bucket recorded in workshop state.

**Windows PowerShell:**

```powershell
.\scripts\08_cleanup.ps1 -Plan `
  -Region us-east-1 `
  -Profile default `
  -StackName kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
./scripts/08_cleanup.sh --plan \
  --region us-east-1 --profile default \
  --stack-name kiro-ws2025-lab
```

Review every resource ID in the output. Stop if it does not match this workshop.

## 2. Execute after explicit approval

**Windows PowerShell:**

```powershell
.\scripts\08_cleanup.ps1 -Execute `
  -Region us-east-1 `
  -Profile default `
  -StackName kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
./scripts/08_cleanup.sh --execute \
  --region us-east-1 --profile default \
  --stack-name kiro-ws2025-lab
```

Type the stack name when prompted. The script acts only on resources recorded in the workshop's `results/` state and applies project/role tag safeguards where available. It then deletes the stack and artifact bucket.

Do not add `-Yes` on Windows or `--yes` on Linux/macOS during the guided workshop; the typed confirmation is intentional.

## 3. Verify deletion

This one-line AWS CLI command works on every workstation:

```text
aws cloudformation describe-stacks --stack-name kiro-ws2025-lab --region us-east-1 --profile default
```

A `ValidationError` stating that the stack does not exist is expected. Also inspect owned AMIs and snapshots carrying the project tag so no retained charges remain.

Preserve non-secret JSON or Markdown evidence if required. Do not retain generated database passwords or dumps.

**Checkpoint:** stack resources, validation instances, retained workshop AMIs/snapshots, ALB, EBS volumes, and artifact bucket are removed.
