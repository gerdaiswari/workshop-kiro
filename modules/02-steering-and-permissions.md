# Module 02 – Create steering, an agent, and tool permissions

## Learning objective

Create Kiro workspace steering and a custom agent yourself. Decide which tools it can use, which are trusted, and where it can save files. The workshop provides example agents to learn from — you can create your own.

## 1. Start a chat with Kiro

From the repository root, start Vibe mode without `--agent`:

```text
kiro-cli chat --v3
```

Ask:

```text
What Kiro workspace configuration folders exist in this repository, and what is
the purpose of steering, agents, skills, hooks, and MCP?
```

This shows that Kiro can read your project files, follow code relationships, and explain your architecture — without you having to configure anything first.

## 2. Create steering

Steering gives Kiro durable instructions and context. Choose its scope based on where the instructions should apply:

- **Global steering** lives in `~/.kiro/steering/` and applies across your workspaces.
- **Workspace steering** lives in this repository's `.kiro/steering/` directory and applies only here.
- `inclusion: always` is for short rules needed in every task.
- `inclusion: manual` is for facts that should be added only to a relevant session.

Run `/context show`. The supplied `.kiro/steering/safety-rules.md` is the always-loaded example. Do not create another copy of the same safety rules: duplication consumes context and can drift.

Instead, create a manual steering file that captures environment facts for this Windows upgrade lab:

```text
Create .kiro/steering/participant-environment.md with manual inclusion. Include:
1. Source and target Windows versions (2019 to 2025)
2. Server roles (APP01 is stateless web apps, DATA01 is stateful databases)
3. Key dependencies (IIS, nginx, Java 17, Node.js 20, SQL Server Express, MySQL, PostgreSQL)
4. Identity model (SSM-only, no domain join)
5. Backup strategy (native database backups on DATA01)
6. Cutover design (APP01 uses ALB target switch; DATA01 is clone-only, not cutover-ready)
7. Rollback method (re-register source APP01 in target group)
8. RTO/RPO (lab has no SLA; mark as "define for production")
9. Maintenance window (lab: anytime; mark as "define for production")
10. Vendor support status for each dependency on Windows Server 2025
```

This gives you a reference for how to describe your own production environment in steering later. Replace the lab values with your real servers, owners, dependencies, and recovery objectives.

Run `/context show` to confirm that `participant-environment.md` is not loaded (because it's marked manual). When you start the adaptation exercise, load it manually with `/context add participant-environment.md`. Then run `/context show` again to verify it's now loaded.

**What you learned:** Kiro can help you create structured documentation with the right format and placeholders — you describe what you need, and it generates the file. Steering controls *when* Kiro loads that context: `always` means safety rules are enforced in every conversation; `manual` means environment-specific facts are only loaded when relevant, saving context budget for the actual task.

## 3. Create a minimal read-only agent

Start plain Kiro again if needed:

```text
kiro-cli chat --v3
```

Ask plain Kiro to set up a workspace agent for this upgrade exercise:

```text
Create .kiro/agents/my-windows-upgrade.json as a minimal read-only custom agent.

Configure it with:
- name: my-windows-upgrade;
- a description that identifies it as a participant-created Windows EC2
  clone-upgrade assistant;
- a prompt that tells it to follow upgrade safety steering, distinguish measured
  facts from assumptions, never treat an AMI clone as live database
  synchronization, never recommend an in-place source upgrade, and require
  evidence before any promotion recommendation;
- only read, grep, glob, and code in both tools and allowedTools;
- only README.md and .kiro/steering/safety-rules.md as file resources; and
- a welcome message that clearly says the agent starts in read-only mode.

Show the proposed JSON and ask for approval before writing it.
```

Review the proposed agent. If you agree, approve the write. If you want different behavior, ask Kiro to revise the prompt or description without weakening the safety boundaries.

This shows that Kiro can help you scaffold configuration files from a natural-language description — you tell it what the agent should do, and it generates valid JSON with the correct schema.

The important fields are:

| Field | Function |
|---|---|
| `name` | Set to `my-windows-upgrade`; this is the name used with `--agent` |
| `description` | Helps people understand when to use the agent |
| `prompt` | Defines its role, behavior, and safety boundaries |
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

This shows that Kiro can help you analyze and reason about your project while respecting the boundaries you defined — it reads code, follows the steering rules, and gives answers grounded in repository files rather than guessing.

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

This shows that Kiro can help you write files and run commands while staying within the guardrails you set — it asks for approval on sensitive actions and respects path/command restrictions, so you stay in control of what actually changes.

## 6. Understand Kiro permissions

Kiro agent permissions use three layers:

1. `tools` — what the agent can attempt.
2. `allowedTools` — what can run automatically without asking.
3. `toolsSettings` — path, command, and service boundaries for a tool.

Approval prompts and agent restrictions are defense in depth. IAM remains authoritative for AWS permissions. Do not use `--trust-all-tools` in this workshop.

## 7. Compare with the supplied reference agents

Only after creating your own agent, compare it with the workshop's reference agents:

- `.kiro/agents/windows-upgrade.json` (orchestrator — works on both Linux/macOS and Windows)
- `.kiro/agents/upgrade-reviewer.json` (read-only independent auditor)
- `.kiro/agents/upgrade-executor.json` (restricted routine executor)

These three agents follow the best-practice trust boundary model: **orchestrator** (plans, coordinates, delegates), **reviewer** (audits evidence, cannot fix), and **executor** (runs approved tasks, cannot decide). They represent one way to configure a full upgrade agent set — yours doesn't need to match them exactly.

Study what they do differently, then decide which features you want to add to `my-windows-upgrade` in later modules. The reference agents are examples to learn from, not mandatory configurations.

> **Windows users:** The consolidated `windows-upgrade.json` accepts both `python3` and `py -3` commands. You do not need a separate agent file.

**Checkpoint:** you created upgrade-focused steering, created and validated `my-windows-upgrade`, ran it, added restricted write/shell tools, observed an approval prompt, and can explain the difference between `tools`, `allowedTools`, and `toolsSettings`.
