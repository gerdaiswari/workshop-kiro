# Module 05 – Create hooks, test safety, and capture baselines

## Learning objective

Create a Kiro `preToolUse` safety hook and a `postToolUse` validation hook, add them to the agent you built in Module 02, verify their behavior locally, and then capture baseline and backup evidence.

## 1. Understand the hook contract

A hook belongs to an agent configuration. It is not a global operating-system file watcher.

This module uses two documented triggers:

| Trigger | Matcher | When it runs |
|---|---|---|
| `preToolUse` | `shell` | Before the agent executes a shell tool request |
| `postToolUse` | `write` | After the agent writes a file |

For `preToolUse`, Kiro sends tool context as JSON on standard input. Exit code `0` allows the tool; exit code `2` blocks it.

## 2. Create your own destructive-command blocker

Start plain Kiro:

```text
kiro-cli chat --v3
```

Ask it to create `scripts/hooks/participant_block_destructive.py` with exactly this content:

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

Review the regex carefully before approving the write. This is intentionally a small learning hook; the supplied `scripts/hooks/block_destructive.py` is the more complete reference implementation.

## 3. Test the hook before attaching it

Exit Kiro. Test a read-only command first.

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

Now test a fake destructive request. This does not call AWS.

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

Do not attach a hook that fails these two tests.

This shows that Kiro can help you write safety automation — you describe what should be blocked, and it generates a working script with the correct input/output contract that you can test independently before trusting it.

## 4. Add hooks to your agent

Use plain Kiro to update `.kiro/agents/my-windows-upgrade.json`. Add a top-level `hooks` object using the command for your workstation.

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

Confirm both hooks are listed. Ask the agent to update `results/participant/agent-permission-test.md`. The path is allowed, so the write may run without another prompt; the quick validator should run afterward. Review the displayed path and diff before continuing.

Do not test a real termination request. The direct fake-input test above proves blocking behavior without creating an AWS API call.

## 6. Compare with the reference hook

Compare your script with `scripts/hooks/block_destructive.py`. Identify differences in JSON error handling, command coverage, and messages.

The reference agents intentionally do not embed one hook command because the Python launcher differs by workstation (`python3` on Linux/macOS and `py -3` on Windows). Your participant agent uses the workstation-specific hook configuration from step 4.

Hooks are defense in depth; they do not replace IAM or human approval.

## 7. Capture baseline tests

Run deterministic tests outside Kiro so the evidence does not depend on model behavior.

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

Results are written under `results/tests/baseline/`. Baseline must pass before an upgrade begins.

## 8. Capture stateful recovery evidence

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
