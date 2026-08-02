# Module 05 – Create hooks, test safety, and capture baselines

## Learning objective

Create a Kiro `preToolUse` safety hook and a `postToolUse` validation hook, add them to the agent you built in Module 02, verify their behavior locally, and then capture baseline and backup evidence.

## Why this matters

Module 02's `deniedCommands` list is a good backstop, but it's a static list you have to remember to update. A hook is a small script *you* write that Kiro runs automatically before or after certain tool calls, so you can add custom logic — like scanning a shell command for dangerous patterns with a regex — without touching the agent JSON schema every time. This module has two parts: first you build and test a safety hook that blocks destructive commands before they run, then you capture "baseline" evidence (what healthy APP01 and DATA01 look like right now) and native database backups, so that after the Windows Server 2025 upgrade you have something concrete to compare against and something to restore from if things go wrong.

## 1. Understand the hook contract

A hook belongs to an agent configuration — it's defined inside the agent's JSON file, not a global setting. It is not a global operating-system file watcher; it only fires for tool calls made by that specific agent.

This module uses two documented triggers:

| Trigger | Matcher | When it runs |
|---|---|---|
| `preToolUse` | `shell` | Before the agent executes a shell tool request |
| `postToolUse` | `write` | After the agent writes a file |

For `preToolUse`, Kiro sends tool context as JSON on standard input — this includes the exact command the agent is about to run, so your hook script can inspect it before it executes. Exit code `0` allows the tool to proceed; exit code `2` blocks it. This is a standard Unix convention (0 = success, nonzero = failure) that Kiro's hook system relies on.

## 2. Create your own destructive-command blocker

Start plain Kiro:

```text
kiro-cli chat --v3
```

Ask it to create `scripts/hooks/participant_block_destructive.py` with exactly this content. This script reads the JSON payload Kiro sends on stdin, checks the shell command against a regex of known-dangerous patterns (instance termination, stack deletion, recursive deletes), and exits with code 2 to block a match or 0 to allow everything else:

```python
#!/usr/bin/env python3
import json
import re
import sys

BLOCKED = re.compile(
    r"aws\s+ec2\s+terminate-instances|"
    r"aws\s+cloudformation\s+delete-stack|"
    r"aws\s+ec2\s+delete-snapshot|"
    r"aws\s+ec2\s+deregister-image|"
    r"rm\s+-rf|"
    r"Remove-Item.*-Recurse",
    re.IGNORECASE,
)

try:
    payload = json.load(sys.stdin)
except (json.JSONDecodeError, OSError) as exc:
    print(f"Invalid hook input: {exc}", file=sys.stderr)
    raise SystemExit(2)

command = str(payload.get("tool_input", {}).get("command", ""))
if BLOCKED.search(command):
    print("Blocked destructive shell command; use a separately reviewed workflow.", file=sys.stderr)
    raise SystemExit(2)

raise SystemExit(0)
```

Review the regex carefully before approving the write — you're about to trust this script to block dangerous commands, so it's worth reading exactly what it matches. This is intentionally a small learning hook; the supplied `scripts/hooks/block_destructive.py` is the more complete reference implementation with broader coverage.

## 3. Test the hook before attaching it

A hook that silently fails to block anything is worse than no hook at all, so test it standalone — by feeding it fake JSON input directly on the command line — before wiring it into your agent. This also means you can test the "blocks a dangerous command" case without any real risk, since you're just piping text into a script, not actually calling AWS.

Exit Kiro. Test a read-only command first — this should be **allowed**, since `describe-instances` only reads data and isn't in the blocked pattern list.

**Windows PowerShell:**

```powershell
'{"tool_input":{"command":"aws ec2 describe-instances"}}' |
  py -3 scripts\hooks\participant_block_destructive.py
$LASTEXITCODE
```

**Linux/macOS Bash:**

```bash
printf '%s' '{"tool_input":{"command":"aws ec2 describe-instances"}}' \
  | python3 scripts/hooks/participant_block_destructive.py
echo $?
```

Expected exit code: `0`.

Now test a fake destructive request — this should be **blocked** (exit code 2), since the command text matches the `terminate-instances` pattern. Note that this test does not call AWS at all; it's purely checking whether your script's regex catches the pattern in a piece of text you're feeding it directly.

**Windows PowerShell:**

```powershell
'{"tool_input":{"command":"aws ec2 terminate-instances --instance-ids i-example"}}' |
  py -3 scripts\hooks\participant_block_destructive.py
$LASTEXITCODE
```

**Linux/macOS Bash:**

```bash
printf '%s' '{"tool_input":{"command":"aws ec2 terminate-instances --instance-ids i-example"}}' \
  | python3 scripts/hooks/participant_block_destructive.py
echo $?
```

Expected exit code: `2`.

Do not attach a hook that fails these two tests — if it doesn't correctly allow the safe command and block the dangerous one now, wiring it into your agent won't fix that; it will just make the failure harder to notice.

This shows that Kiro can help you write safety automation — you describe what should be blocked, and it generates a working script with the correct input/output contract that you can test independently before trusting it.

## 4. Add hooks to your agent

Now that you've proven the script works standalone, wire it into the agent so Kiro actually calls it automatically. Use plain Kiro to update `.kiro/agents/my-windows-upgrade.json`. Add a top-level `hooks` object using the command for your workstation — the `preToolUse` hook runs your blocker script before every shell command, and the `postToolUse` hook runs the repository's quick validator after every file write, so mistakes get caught immediately rather than at the end of a session.

**Windows hook configuration:**

```json
"hooks": {
  "preToolUse": [
    {
      "matcher": "shell",
      "command": "py -3 scripts\\hooks\\participant_block_destructive.py",
      "timeout_ms": 10000
    }
  ],
  "postToolUse": [
    {
      "matcher": "write",
      "command": "py -3 tests\\static\\validate_repo.py --quick",
      "timeout_ms": 30000
    }
  ]
}
```

**Linux/macOS hook configuration:**

```json
"hooks": {
  "preToolUse": [
    {
      "matcher": "shell",
      "command": "python3 scripts/hooks/participant_block_destructive.py",
      "timeout_ms": 10000
    }
  ],
  "postToolUse": [
    {
      "matcher": "write",
      "command": "python3 tests/static/validate_repo.py --quick",
      "timeout_ms": 30000
    }
  ]
}
```

The backslashes in Windows JSON are doubled because JSON uses `\` as an escape character.

Validate your updated agent:

**Windows PowerShell:**

```powershell
kiro-cli agent validate --path .kiro\agents\my-windows-upgrade.json
```

**Linux/macOS Bash:**

```bash
kiro-cli agent validate --path .kiro/agents/my-windows-upgrade.json
```

## 5. Verify the hooks inside Kiro

Start your agent:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Inside chat:

```text
/hooks
```

Confirm both hooks are listed — this is Kiro's way of showing you exactly what's wired up for the active agent, so you can double-check before trusting it in a real task. Ask the agent to update `results/participant/agent-permission-test.md`. The path is allowed, so the write may run without another prompt; the quick validator should run afterward as your `postToolUse` hook. Review the displayed path and diff before continuing.

Do not test a real termination request. The direct fake-input test above (step 3) already proves the blocking behavior works, without needing to risk an actual AWS API call.

## 6. Compare with the reference hook

Compare your script with `scripts/hooks/block_destructive.py`. Identify differences in JSON error handling, command coverage, and messages — this is a useful exercise for seeing what a production-grade version of the same idea looks like.

The reference agents intentionally do not embed one hardcoded hook command because the Python launcher differs by workstation (`python3` on Linux/macOS and `py -3` on Windows). Your participant agent uses the workstation-specific hook configuration from step 4.

Hooks are defense in depth; they do not replace IAM or human approval. Think of them as one more layer that catches mistakes early, not the only thing standing between you and a destructive action.

## 7. Capture baseline tests

Run deterministic tests outside Kiro so the evidence does not depend on model behavior — this is the "before" snapshot of APP01 and DATA01 while they're healthy on Windows Server 2019, which you'll compare against after the upgrade in Module 07 to prove nothing regressed.

**Windows PowerShell:**

```powershell
py -3 scripts\03_run_tests.py `
  --phase baseline `
  --region us-east-1 `
  --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/03_run_tests.py \
  --phase baseline \
  --region us-east-1 \
  --stack-name kiro-ws2025-lab
```

Results are written under `results/tests/baseline/`. Baseline must pass before an upgrade begins — if the servers already have failing tests before you touch anything, you'd have no way to tell whether a later failure was caused by the upgrade or was already there.

## 8. Capture stateful recovery evidence

DATA01 runs three database engines, so before any upgrade touches it, take a native backup — a real, restorable database backup, independent of the AMI snapshot AWS creates during clone-upgrade. This guarantees you have a way back even if the clone-upgrade process itself goes wrong.

**Windows PowerShell:**

```powershell
py -3 scripts\03_run_tests.py `
  --phase backup-data `
  --region us-east-1 `
  --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/03_run_tests.py \
  --phase backup-data \
  --region us-east-1 \
  --stack-name kiro-ws2025-lab
```

Backups remain on DATA01 for this synthetic lab. Production backups require controlled storage and an independently tested restore.

## Transfer to your environment

- **Lab exercise:** a small regex hook blocks selected commands; supplied scripts capture synthetic endpoint/database baselines and local native backups.
- **Reusable pattern:** combine least-privilege IAM, restricted tools, human approval, hooks, deterministic tests, native backups, and tested restore procedures. A hook is defense in depth, not a security boundary by itself.
- **Adapt before reuse:** build business/API/data assertions for each application, review every destructive command family, store backups in approved protected storage, test restore independently, and define retention plus recovery ownership from RTO/RPO.

Adaptation prompt:

```text
Review my planned safety controls and baseline tests. Identify what is enforced
by IAM, agent permissions, hooks, scripts, human approval, and recovery testing.
Find gaps; do not assume the lab regex or test pack covers my workload.
```

**Checkpoint:** you created and tested a hook script, attached both supported hooks to your own agent, validated the agent, saw `/hooks`, and captured passing APP01/DATA01 baseline and native-backup evidence.
