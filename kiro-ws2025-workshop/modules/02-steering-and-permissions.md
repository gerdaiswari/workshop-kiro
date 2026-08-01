# Module 02 – Create steering, an agent, and tool permissions

## Learning objective

Create Kiro workspace steering and a custom agent yourself. Decide which tools it can use, which are trusted, and where it can save files. The workshop provides example agents to learn from — you can create your own.

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

Steering is persistent project context that Kiro reads at the start of every session. In this step, you'll create a steering file focused on the **Windows upgrade process** — the rules that protect you during the clone-upgrade itself.

Review the example below. If you agree with these rules, you can copy and paste them directly. If you want different rules, write your own — the important thing is that your steering captures **upgrade-process safety**, not general lab setup.

At the plain Kiro prompt, enter:

```text
Create .kiro/steering/participant-upgrade-safety.md with these rules:
- Never upgrade a source instance in place; always use the clone-upgrade runbook.
- The AWS runbook does not support domain controllers, clusters, desktop Windows, RDSH, RDCB, RDVH, or RDWA.
- Clone upgrade requires Nitro instance type, SSM Agent online, TLS 1.2, PowerShell 3+, 20 GB free on boot volume, and outbound internet.
- Treat DATA01 as stateful; an AMI clone is point-in-time and is not database replication.
- Capture baseline evidence before upgrade and post-upgrade evidence before promotion.
- Test failure blocks promotion. Fix the validation instance; do not weaken the test.
Show the proposed file and ask for approval before writing it.
```

Approve only after the content matches your intent. You can add, remove, or rephrase rules — this is **your** steering file.

Exit and restart Kiro so the new steering file is loaded, then ask:

```text
Summarize the upgrade safety rules that apply to this workspace.
```

**What you learned:** files under `.kiro/steering/` give every workspace session durable project context. Keep steering factual, concise, and focused on the process it governs. Your upgrade steering should capture the constraints of the clone-upgrade runbook — not general lab infrastructure rules.

## 3. Create a minimal read-only agent

Start plain Kiro again if needed:

```text
kiro-cli chat --v3
```

Now create your own agent focused on the Windows upgrade process. Review the example below — if it fits your needs, use it directly. Otherwise, adjust the prompt and description to match how you want your agent to behave.

Ask Kiro to create `.kiro/agents/my-windows-upgrade.json` with exactly this configuration:

```json
{
  "name": "my-windows-upgrade",
  "description": "Participant-created read-only Windows upgrade assistant focused on clone-upgrade safety.",
  "prompt": "You are a cautious Windows EC2 upgrade assistant. Focus on the clone-upgrade process from Windows Server 2019 to 2025. Use workspace steering for upgrade constraints. Distinguish facts from assumptions. Never claim that an AMI clone synchronizes a live database. Never recommend in-place upgrade of a source instance.",
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

Only after creating your own agent, compare it with the workshop's reference agents:

- `.kiro/agents/windows-upgrade.json` (Linux/macOS)
- `.kiro/agents/windows-upgrade-windows.json` (Windows)

These reference agents add AWS service boundaries, hooks, MCP, the workshop skill, and subagent support. They represent one way to configure a full upgrade agent — yours doesn't need to match them exactly.

Study what they do differently, then decide which features you want to add to `my-windows-upgrade` in later modules. The reference agents are examples to learn from, not mandatory configurations.

**Checkpoint:** you created upgrade-focused steering, created and validated `my-windows-upgrade`, ran it, added restricted write/shell tools, observed an approval prompt, and can explain the difference between `tools`, `allowedTools`, and `toolsSettings`.
