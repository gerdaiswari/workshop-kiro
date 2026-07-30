# Module 02 – Configure Kiro steering, agent, and tool trust

## Learning objective
Start a workspace custom agent, understand what context it inherits, and verify that read-only tools are trusted while mutations still require approval.

## 1. Inspect the workspace configuration

Kiro discovers workspace configuration only when you start it from the repository directory.

**Windows PowerShell:**

```powershell
Get-ChildItem .kiro\steering, .kiro\skills, .kiro\agents -Recurse -File
```

**Linux/macOS Bash:**

```bash
find .kiro/steering .kiro/skills .kiro/agents -type f -maxdepth 4 -print
```

The folders have different purposes:

- `.kiro/steering/` records persistent project rules and facts.
- `.kiro/skills/` contains reusable procedures loaded when relevant.
- `.kiro/agents/` defines each custom agent's prompt, tools, trusted tools, restrictions, resources, and hooks.

## 2. Validate and list the agents

Validate the main agent for your workstation, then list all agents.

**Windows PowerShell:**

```powershell
kiro-cli agent validate --path .kiro\agents\windows-upgrade-windows.json
kiro-cli agent list
```

**Linux/macOS Bash:**

```bash
kiro-cli agent validate --path .kiro/agents/windows-upgrade.json
kiro-cli agent list
```

The selected agent (`windows-upgrade-windows` on Windows or `windows-upgrade` on Linux/macOS) should appear under **Workspace**. If it does not, confirm that your terminal is in the repository root.

The complete automated check is:

**Windows:**

```powershell
py -3 scripts\check_kiro_prereqs.py
```

**Linux/macOS:**

```bash
python3 scripts/check_kiro_prereqs.py
```

## 3. Understand tool trust

The agent configuration uses documented Kiro fields:

- `tools` lists tools the agent may request.
- `allowedTools` lists tools that run without an approval prompt.
- `toolsSettings` restricts writable paths, shell commands, and AWS services.
- `hooks.preToolUse` runs the destructive-command blocker before shell execution.
- `hooks.postToolUse` runs the quick validator after the agent writes a file.

Read, grep, glob, code intelligence, and AWS Knowledge MCP are trusted. Writes and AWS mutations are not in `allowedTools`, so Kiro asks before using them. Always read the proposed action before approving it.

Do **not** start this workshop with `--trust-all-tools`; that bypasses the approval prompts the exercise is designed to demonstrate.

## 4. Start the workshop agent with the v3 engine

**Windows:**

```text
kiro-cli chat --v3 --agent windows-upgrade-windows
```

**Linux/macOS:**

```text
kiro-cli chat --v3 --agent windows-upgrade
```

At the Kiro prompt, enter:

```text
Summarize the workshop safety boundary and list actions requiring explicit approval. Do not call AWS and do not modify files.
```

Use these documented slash commands inside the chat:

```text
/tools
/hooks
/help
```

`/tools` shows available tools. `/hooks` should show the `preToolUse` and `postToolUse` hooks loaded from the agent configuration.

## 5. Verify the safety hook without changing AWS

Exit Kiro first, then test the hook directly.

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

Expected exit code: `2`. This is a local test with a fake instance ID; it does not call AWS.

**Checkpoint:** the workstation-specific agent validates and appears in `kiro-cli agent list`, `/hooks` shows two supported hooks, and the local blocker exits with code 2.
