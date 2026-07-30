# Module 05 – Hooks, approvals, and baseline tests

## Learning objective
Understand Kiro's supported agent hooks, verify the destructive-command blocker locally, and capture baseline and backup evidence before any upgrade.

## 1. Inspect the active hook configuration

Hooks are defined inside the main agent file for each workstation:

| Workstation | Agent file | Python launcher used by hooks |
|---|---|---|
| Windows | `.kiro/agents/windows-upgrade-windows.json` | `py -3` |
| Linux/macOS | `.kiro/agents/windows-upgrade.json` | `python3` |

Both agents use the same documented triggers:

| Trigger | Matcher | Purpose |
|---|---|---|
| `preToolUse` | `shell` | Run `scripts/hooks/block_destructive.py` before matching shell operations |
| `postToolUse` | `write` | Run `tests/static/validate_repo.py --quick` after Kiro write-tool operations |

Start the hook-enabled agent for your workstation and inspect loaded hooks.

**Windows:** `kiro-cli chat --v3 --agent windows-upgrade-windows`

**Linux/macOS:** `kiro-cli chat --v3 --agent windows-upgrade`

Inside chat:

```text
/hooks
```

A `preToolUse` hook blocks a matching tool call when its command exits with code 2. The post-write validator runs only after Kiro uses its `write` tool; it is not a general operating-system file watcher.

## 2. Test the blocker locally

Exit Kiro before running this test. The example contains a fake instance ID and does not call AWS.

**Windows PowerShell:**

```powershell
'{"tool_input":{"command":"aws ec2 terminate-instances --instance-ids i-example"}}' |
  py -3 scripts\hooks\block_destructive.py
$LASTEXITCODE
```

**Linux/macOS Bash:**

```bash
printf '%s' '{"tool_input":{"command":"aws ec2 terminate-instances --instance-ids i-example"}}' \
  | python3 scripts/hooks/block_destructive.py
echo $?
```

Expected exit code: `2`. A read-only `aws ec2 describe-instances` example should exit `0`.

Hooks are defense in depth. IAM and careful review of each approval prompt remain the primary safety boundaries.

## 3. Capture baseline tests

**Windows PowerShell:**

```powershell
py -3 scripts\03_run_tests.py `
  --phase baseline `
  --region us-east-1 --profile default `
  --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/03_run_tests.py \
  --phase baseline \
  --region us-east-1 --profile default \
  --stack-name kiro-ws2025-lab
```

Results are written under `results/tests/baseline/`. Baseline must pass before an upgrade begins.

## 4. Capture stateful recovery evidence

**Windows PowerShell:**

```powershell
py -3 scripts\03_run_tests.py `
  --phase backup-data `
  --region us-east-1 --profile default `
  --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/03_run_tests.py \
  --phase backup-data \
  --region us-east-1 --profile default \
  --stack-name kiro-ws2025-lab
```

Backups remain on DATA01 for this synthetic lab. Production backups require controlled storage and an independently tested restore.

**Checkpoint:** `/hooks` shows both hooks, the blocker exits 2 for the fake destructive command, APP01 and DATA01 baseline checks pass, and native backup checks pass.
