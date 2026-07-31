# Module 02 – Create steering, an agent, and tool permissions

## Learning objective

Create Kiro workspace steering and a custom agent yourself, then control which tools it can use, which tools are trusted, and where it may write. The finished agents supplied with the workshop are references—not a substitute for this exercise.

## 1. Start with plain Kiro

From the repository root, start Vibe mode without `--agent`:

```text
kiro-cli chat --v3
```

Ask:

```text
What Kiro workspace configuration folders exist in this repository, and what is
the purpose of steering, agents, skills, hooks, and MCP? Read only; do not edit.
```

This establishes the starting point: plain Kiro has general capabilities but no role tailored to your upgrade exercise.

## 2. Create your own steering file

Steering is persistent project context. Instead of only reading the supplied steering, create a participant-owned file.

At the plain Kiro prompt, enter:

```text
Create .kiro/steering/participant-safety.md with these rules:
- This is a Windows Server 2019 to 2025 clone-upgrade workshop in us-east-1.
- Never upgrade a source instance in place.
- Never delete AWS resources without explicit approval in the current turn.
- Treat DATA01 as stateful; an AMI copy is not database synchronization.
- Require baseline and post-upgrade evidence before recommending promotion.
Show the proposed file and ask for approval before writing it.
```

Approve only after the content matches the five rules. Exit and restart Kiro so the new steering file is loaded, then ask:

```text
Summarize the upgrade safety rules that apply to this workspace.
```

**What you learned:** files under `.kiro/steering/` give every workspace session durable project context. Keep steering factual, concise, and applicable across tasks.

## 3. Create a minimal read-only agent

Start plain Kiro again if needed:

```text
kiro-cli chat --v3
```

Ask Kiro to create `.kiro/agents/my-windows-upgrade.json` with exactly this configuration:

```json
{
  "name": "my-windows-upgrade",
  "description": "Participant-created read-only Windows upgrade learning agent.",
  "prompt": "You are a cautious Windows EC2 upgrade assistant. Use workspace steering, distinguish facts from assumptions, and never claim that an AMI clone synchronizes a live database.",
  "tools": [
    "read",
    "grep",
    "glob",
    "code"
  ],
  "allowedTools": [
    "read",
    "grep",
    "glob",
    "code"
  ],
  "resources": [
    "file://README.md",
    "file://.kiro/steering/**/*.md"
  ],
  "welcomeMessage": "My Windows upgrade learning agent is ready in read-only mode."
}
```

The important fields are:

| Field | Function |
|---|---|
| `name` | Name used with `--agent` |
| `description` | Helps people understand when to use the agent |
| `prompt` | Defines its role and behavior |
| `tools` | Tools the agent is able to request |
| `allowedTools` | Tools trusted to run without an approval prompt |
| `resources` | Workspace files loaded as agent context |

Exit Kiro and validate the file.

**Windows PowerShell:**

```powershell
kiro-cli agent validate --path .kiro\agents\my-windows-upgrade.json
```

**Linux/macOS Bash:**

```bash
kiro-cli agent validate --path .kiro/agents/my-windows-upgrade.json
```

Then confirm discovery:

```text
kiro-cli agent list
```

Do not continue until validation succeeds.

## 4. Run the agent you created

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Ask:

```text
Using the workspace steering, explain why APP01 and DATA01 need different
cutover designs. Cite the repository files that support your answer.
```

Inside chat, run:

```text
/tools
```

The agent should expose only read-oriented tools. It cannot write files, run shell commands, or call AWS because those tools are not in `tools`.

## 5. Add write and shell tools with restrictions

Exit the custom agent and return to plain Kiro. Ask it to update `my-windows-upgrade.json` as follows:

1. Add `write` and `shell` to `tools`.
2. Keep them out of `allowedTools`, so each use requires approval.
3. Add this `toolsSettings` object:

```json
"toolsSettings": {
  "write": {
    "allowedPaths": [
      "./results/participant/**"
    ],
    "deniedPaths": [
      "./.env",
      "./**/*.pem",
      "./.kiro/**"
    ]
  },
  "shell": {
    "allowedCommands": [
      "python3 tests/static/validate_repo.py*",
      "py -3 tests/static/validate_repo.py*",
      "git status*",
      "git diff*"
    ],
    "deniedCommands": [
      "aws ec2 terminate-instances*",
      "aws cloudformation delete-stack*",
      "rm -rf *",
      "Remove-Item * -Recurse*"
    ],
    "autoAllowReadonly": true,
    "denyByDefault": false
  }
}
```

Validate the agent again, restart it, and inspect `/tools`.

Test the allowed path:

```text
Create results/participant/agent-permission-test.md containing one sentence
that says this file was created after participant approval.
```

Kiro should request approval because `write` is not in `allowedTools`. Review the path and approve it.

Then test the boundary:

```text
Replace README.md with the text "permission test".
```

Reject the request if Kiro asks. The configured write boundary should prevent that path, but the participant remains responsible for reviewing every proposed action.

## 6. Understand Kiro permissions

Kiro agent permissions use three layers:

1. `tools` — what the agent can attempt.
2. `allowedTools` — what can run automatically without asking.
3. `toolsSettings` — path, command, and service boundaries for a tool.

Approval prompts and agent restrictions are defense in depth. IAM remains authoritative for AWS permissions. Do not use `--trust-all-tools` in this workshop.

## 7. Compare with the supplied reference agents

Only after creating your own agent, compare it with:

- `.kiro/agents/windows-upgrade.json` for Linux/macOS
- `.kiro/agents/windows-upgrade-windows.json` for Windows

The reference agents add AWS service boundaries, hooks, MCP, the workshop skill, and subagent support. Later modules will have you add those features to `my-windows-upgrade` yourself.

**Checkpoint:** you created steering, created and validated `my-windows-upgrade`, ran it, added restricted write/shell tools, observed an approval prompt, and can explain the difference between `tools`, `allowedTools`, and `toolsSettings`.
