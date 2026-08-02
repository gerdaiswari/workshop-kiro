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

Instead, ask Kiro to create a manual steering file that captures environment facts for this Windows upgrade:

```text
Create .kiro/steering/participant-environment.md with manual inclusion. Include:
1. Source OS: Windows Server 2019
2. Target OS: Windows Server 2025
3. Servers: APP01 (stateless web), DATA01 (stateful databases)
4. Upgrade method: AWS SSM clone-upgrade (not in-place)
5. Cutover: APP01 uses ALB target switch; DATA01 is validation-only
6. Rollback: re-register source in ALB target group
7. RTO: 4 hours
8. RPO: 1 hour
```

This gives you a reference for how to describe your own servers in steering later. Replace the values with your real server names, roles, and recovery objectives.

Run `/context show` to confirm that `participant-environment.md` is not loaded (because it's marked manual). When you start the adaptation exercise, load it manually with `/context add .kiro/steering/participant-environment.md`. Then run `/context show` again to verify it's now loaded.

**What you learned:** Kiro can help you create structured documentation — you describe what you need, and it generates the file with the right format.

## 3. Create a custom agent

Start plain Kiro:

```text
kiro-cli chat --v3
```

Ask Kiro to create a custom agent for this upgrade exercise:

```text
Create .kiro/agents/my-windows-upgrade.json as a read-only agent. Include:
1. Role: Windows EC2 clone-upgrade assistant
2. Behavior: follow all workspace steering, use only measured evidence, call out
   anything that's not verified, never recommend in-place source upgrade
3. tools and allowedTools: ["read", "grep", "glob", "code"]
5. Resources: file://README.md, file://.kiro/steering/**/*.md, and file://inventory/assumed-inventory.yaml
6. Welcome message: says the agent starts in read-only mode
```

Review the proposed file. Exit Kiro and validate:

**Linux/macOS:**

```bash
kiro-cli agent validate --path .kiro/agents/my-windows-upgrade.json
kiro-cli agent list
```

**Windows PowerShell:**

```powershell
kiro-cli agent validate --path .kiro\agents\my-windows-upgrade.json
kiro-cli agent list
```

Your agent should appear in the workspace list. Then upgrade it to V3:

```text
kiro-cli chat --v3
```

Run `/upgrade-agent` and select the workspace agents. This adds the `permissions` block that V3 needs to load the agent with `--agent`.

Now start your agent:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

## 4. Compare: with agent vs without agent

First, ask the same question **without** a custom agent:

```text
kiro-cli chat --v3
```

```text
Explain why APP01 and DATA01 need different cutover designs.
```

Notice: plain Kiro gives a general answer. It may not reference your steering rules or flag unverified claims.

Now ask the same question **with** your custom agent:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

```text
Explain why APP01 and DATA01 need different cutover designs.
```

Notice the difference:
- The agent follows your steering (safety rules, environment profile)
- It cites specific repository files as evidence
- It marks anything unverified as unverified
- It refuses to recommend in-place upgrades

> **Key takeaway:** A custom agent gives Kiro a consistent role, loads relevant context automatically, and enforces behavior boundaries you defined. Without an agent, Kiro is helpful but generic.

Inside chat, run `/tools` to see what's available. Then try asking it to run a command:

```text
Run git status
```

The agent should refuse — it doesn't have `shell` in its tools, so it cannot execute commands. This proves that tool boundaries limit what the agent can do.

## 5. Add write and shell with permissions

Ask Kiro to update your agent with write and shell capabilities:

```text
Update .kiro/agents/my-windows-upgrade.json:
1. Give the agent write and shell capabilities, but require approval before each use
2. Only allow writing to ./results/participant/ — block .env, .pem, and .kiro/
3. Only allow running: validate_repo.py, git status, git diff
4. Block dangerous commands: terminate-instances, delete-stack, rm -rf, Remove-Item -Recurse
```

After Kiro updates the file, exit and validate:

**Linux/macOS:**

```bash
kiro-cli agent validate --path .kiro/agents/my-windows-upgrade.json
```

**Windows PowerShell:**

```powershell
kiro-cli agent validate --path .kiro\agents\my-windows-upgrade.json
```

Then start a new session and run `/upgrade-agent` to update V3 permissions. Start your agent:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Test the allowed path:

```text
Create results/participant/agent-permission-test.md containing one sentence
that says this file was created by the agent within the allowed path.
```

Then test the boundary:

```text
Replace README.md with the text "permission test".
```

After `/upgrade-agent`, the V3 permissions use **deny** as a hard block. The `deny > ask > allow` resolution means deny always wins.

## 6. Understand permissions

After `/upgrade-agent`, your agent has a `permissions` block with three effects:

| Effect | What happens | Can user override? |
|---|---|---|
| `deny` | Hard block — tool call is rejected | No |
| `ask` | Kiro asks for approval before running | Yes |
| `allow` | Runs automatically, no prompt | N/A |

Permissions are the enforcement layer. `toolsSettings` (V2 fields) define the boundaries; `/upgrade-agent` converts them into hard `permissions.rules`.

## 7. Compare with the supplied reference agents

Only after creating your own agent, compare it with the workshop's reference agents:

- `.kiro/agents/windows-upgrade.json` (orchestrator — works on both Linux/macOS and Windows)
- `.kiro/agents/upgrade-reviewer.json` (read-only independent auditor)
- `.kiro/agents/upgrade-executor.json` (restricted routine executor)

These three agents follow the best-practice trust boundary model: **orchestrator** (plans, coordinates, delegates), **reviewer** (audits evidence, cannot fix), and **executor** (runs approved tasks, cannot decide). They represent one way to configure a full upgrade agent set — yours doesn't need to match them exactly.

Study what they do differently, then decide which features you want to add to `my-windows-upgrade` in later modules. The reference agents are examples to learn from, not mandatory configurations.

> **Windows users:** The consolidated `windows-upgrade.json` accepts both `python3` and `py -3` commands. You do not need a separate agent file.

**Checkpoint:** you created upgrade-focused steering, created and validated `my-windows-upgrade`, ran it, added restricted write/shell tools, observed an approval prompt, and can explain the difference between `tools`, `allowedTools`, and `toolsSettings`.
