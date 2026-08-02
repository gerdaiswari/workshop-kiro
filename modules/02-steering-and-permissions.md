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
Create .kiro/agents/my-windows-upgrade.md as a V3 agent in Markdown format. Include:
1. Role: Windows EC2 clone-upgrade assistant
2. Behavior: follow all workspace steering, use only measured evidence, call out
   anything that's not verified, never recommend in-place source upgrade
3. Tools: read only
4. Resources: README.md, all steering files, and the inventory
5. Permissions: allow fs_read
6. Welcome message: says the agent starts in read-only mode
```

Review the proposed file. V3 agents use Markdown — your system prompt is the document body, configuration is in YAML frontmatter.

Exit Kiro and validate:

**Windows PowerShell:**

```powershell
kiro-cli agent validate --path .kiro\agents\my-windows-upgrade.md
```

**Linux/macOS Bash:**

```bash
kiro-cli agent validate --path .kiro/agents/my-windows-upgrade.md
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

You'll see `read` (includes file reading, search, and diagnostics) and `write`. Even though `write` appears in the list, the agent's permissions only allow `fs_read` — any write attempt will be blocked or require approval. Shell and AWS tools are not available.

This shows that Kiro can help you analyze and reason about your project while respecting the permissions you defined — it reads code, follows the steering rules, and gives answers grounded in repository files.

## 5. Set up permissions (hard limits)

Permissions control what the agent can and cannot do. In V3, they go directly in the agent's YAML frontmatter.

Ask Kiro to update your agent with write/shell capabilities and permissions:

```text
Update .kiro/agents/my-windows-upgrade.md:
1. Give the agent write and shell capabilities (add to tools)
2. Add permissions rules:
   - Allow writing only to results/participant/
   - Hard deny writing to .env, .pem, and .kiro/
   - Allow running: validate_repo.py, git status, git diff
   - Hard deny: terminate-instances, delete-stack, rm -rf
```

Three effects control the behavior:

| Effect | What happens | Can user override? |
|---|---|---|
| `deny` | Hard block — tool call is rejected | No |
| `ask` | Kiro asks for approval before running | Yes (user must confirm) |
| `allow` | Runs automatically, no prompt | N/A |

Resolution order: **deny > ask > allow**. A deny rule always wins.

Test the hard limit — start your agent:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Try:

```text
Replace README.md with the text "permission test".
```

This is **hard blocked** by the deny rule — it will not proceed even if you say "yes".

Then test the allowed path:

```text
Create results/participant/agent-permission-test.md containing one sentence
that says this file was created by the agent within the allowed path.
```

This writes directly because `results/participant/` has `effect: allow`.

## 6. Understand the permission layers

| Layer | What it does |
|---|---|
| **Permissions** (deny/ask/allow in agent frontmatter) | Hard control over what tools can do |
| **Hooks** (preToolUse scripts) | Custom logic that blocks specific patterns |
| **IAM** | AWS API authorization |

Permissions are the primary enforcement. Hooks add custom logic (Module 05). IAM is the final authority for AWS calls.

## 7. Compare with the supplied reference agents

Only after creating your own agent, compare it with the workshop's reference agents:

- `.kiro/agents/windows-upgrade.md` (orchestrator — works on both Linux/macOS and Windows)
- `.kiro/agents/upgrade-reviewer.md` (read-only independent auditor)
- `.kiro/agents/upgrade-executor.md` (restricted routine executor)

These three agents follow the best-practice trust boundary model: **orchestrator** (plans, coordinates, delegates), **reviewer** (audits evidence, cannot fix), and **executor** (runs approved tasks, cannot decide). They represent one way to configure a full upgrade agent set — yours doesn't need to match them exactly.

Study what they do differently, then decide which features you want to add to `my-windows-upgrade` in later modules. The reference agents are examples to learn from, not mandatory configurations.

> **Windows users:** The consolidated `windows-upgrade.json` accepts both `python3` and `py -3` commands. You do not need a separate agent file.

**Checkpoint:** you created upgrade-focused steering, created and validated `my-windows-upgrade`, ran it, added restricted write/shell tools, observed an approval prompt, and can explain the difference between `tools`, `allowedTools`, and `toolsSettings`.
