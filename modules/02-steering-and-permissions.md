# Module 02 – Create steering, an agent, and tool permissions

## Learning objective

Create workspace steering and a restricted custom agent, convert the agent once for Kiro CLI V3, and verify its allowed and denied operations with harmless tests.

## Why this matters

So far you have used Kiro's default, unrestricted agent. In a real upgrade project you don't want every session to have unlimited read/write/shell access — you want an agent that always follows your safety rules, can only write to specific folders, and can only run a short allowlist of shell commands. This module builds exactly that: a custom agent scoped down to what a Windows-upgrade assistant actually needs, plus durable "steering" instructions that travel with every session in this repository. You'll create the agent, prove its restrictions work with harmless test commands, and compare it against the reference agents already included in the repo.

## 1. Start a chat with Kiro

From the repository root:

```text
kiro-cli chat --v3
```

Ask:

```text
What Kiro workspace configuration folders exist in this repository, and what is
the purpose of steering, agents, skills, hooks, and MCP?
```

This shows that Kiro can inspect project files and explain how the workspace is organized.

## 2. Create steering

Steering gives Kiro durable instructions and context — think of it as a set of standing notes that Kiro re-reads every time it's relevant, so you never have to repeat the same safety rules or project facts in every prompt.

- **Global steering** lives in `~/.kiro/steering/` and applies across workspaces (every repository you open on your machine).
- **Workspace steering** lives in `.kiro/steering/` and applies only to this repository.
- `inclusion: always` loads a file automatically into every session, with no action needed.
- `inclusion: manual` loads a file only when you explicitly add it with `/context add` — useful for reference material you only want in context sometimes, so it doesn't crowd out other information by default.

Run `/context show`. The supplied `.kiro/steering/safety-rules.md` is the always-loaded example — you should see it listed without doing anything else, because `inclusion: always` files are loaded automatically at session start.

Ask Kiro to create a manual environment profile:

```text
Create .kiro/steering/participant-environment.md with `inclusion: manual`. Include:
1. Source OS: Windows Server 2019
2. Target OS: Windows Server 2025
3. Servers: APP01 (stateless web), DATA01 (stateful databases)
4. Upgrade method: AWS SSM clone-upgrade (not in-place)
5. Cutover: APP01 uses an ALB target switch; DATA01 is validation-only
6. Rollback: re-register source APP01 in the ALB target groups
7. RTO: 4 hours
8. RPO: 1 hour
```

Now prove to yourself that manual steering behaves differently from always-loaded steering. Run `/context show` to confirm the new file is **not** loaded yet — manual files stay out of context until you ask for them. Then manually add it with `/context add .kiro/steering/participant-environment.md`. Run `/context show` again — the file should now appear in the list, because you explicitly opted it in for this session.

```text
/context show
/context add .kiro/steering/participant-environment.md
/context show
```

## 3. Create the restricted custom agent

A custom agent is a JSON file that defines a named Kiro persona with its own tool access, write/shell restrictions, and behavior prompt. Instead of trusting Kiro with everything by default, you list exactly which tools it can use, which of those it can use *without* asking you first, and which paths or commands are explicitly blocked. You're about to build one scoped for this Windows-upgrade workshop: it can read and analyze freely, but its writes and shell commands are locked down to a small, reviewed set.

Start plain Kiro if needed:

```text
kiro-cli chat --v3
```

Ask Kiro:

```text
Create .kiro/agents/my-windows-upgrade.json using the documented JSON agent schema.
Use these exact fields:
1. name: my-windows-upgrade
2. description: Participant-created Windows EC2 clone-upgrade assistant
3. prompt: Follow workspace steering; use measured evidence; call out unverified
   facts; never recommend an in-place source upgrade
4. tools: ["read", "write", "grep", "glob", "shell"]
5. allowedTools: ["read", "grep", "glob"]
6. resources: ["file://README.md", "file://.kiro/steering/**/*.md",
   "file://inventory/assumed-inventory.yaml"]
7. toolsSettings.write:
   - allowedPaths: ["./results/participant/**"]
   - deniedPaths: ["./results/blocked/**", "./README.md", "./.env",
     "./**/*.pem", "./.kiro/**"]
8. toolsSettings.shell:
   - allowedCommands: ["python3 tests/static/validate_repo.py*",
     "py -3 tests/static/validate_repo.py*", "git status*", "git diff*"]
   - deniedCommands: ["echo blocked-test", "aws ec2 terminate-instances*",
     "aws cloudformation delete-stack*", "rm -rf *",
     "Remove-Item * -Recurse*"]
   - autoAllowReadonly: false
   - denyByDefault: true
9. welcomeMessage: explain that writes and shell commands are restricted

Use `prompt`, not a `role` field. Show the proposed JSON and ask before writing it.
```

A quick guide to what each field does:

- `tools` — the full list of capabilities this agent is even allowed to request (read, write, grep, glob, shell). Anything not listed here is unavailable no matter what.
- `allowedTools` — a subset of `tools` that Kiro can use *without pausing to ask you* for approval each time. Here that's just read-only inspection (`read`, `grep`, `glob`); every write and shell request will still prompt you.
- `toolsSettings.write.allowedPaths` / `deniedPaths` — even when a write is approved, it can only land under `results/participant/**`. Sensitive files like `.env`, `.pem` keys, and the `.kiro/` config folder are explicitly denied so the agent can never touch them, even by mistake.
- `toolsSettings.shell.allowedCommands` / `deniedCommands` — the agent can only run a short allowlist of harmless commands (running the validator script, `git status`, `git diff`). Destructive AWS calls and recursive deletes (`rm -rf *`) are explicitly denied as a backstop, and `denyByDefault: true` means anything not on the allowlist is refused rather than silently permitted.

Exit Kiro and validate from the repository root. `agent validate` checks that the JSON file matches the schema Kiro expects (correct field names, valid values) — it doesn't check AWS permissions, just that the file itself is well-formed and usable.

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

Do not continue until validation succeeds and `my-windows-upgrade` appears as a workspace agent in the `agent list` output — that confirms Kiro can discover and load it.

## 4. Convert workspace agents for V3

The JSON you just created uses the portable V2 fields (`allowedTools` and `toolsSettings`) — these work across Kiro CLI versions, but Kiro's newer V3 "trust engine" reads a different, more granular permission format (`permissions.rules`). The `/upgrade-agent` command translates your V2 fields into the equivalent V3 rules automatically, so you don't have to hand-write both formats. Run this conversion once so your agent's restrictions are actually enforced under V3:

```text
kiro-cli chat --v3
```

Inside chat, run:

```text
/upgrade-agent
```

Select **V2 Workspace** — this tells Kiro to convert the agent files that live in this repository's `.kiro/agents/` folder (as opposed to global agents in your home directory, which are unrelated to this workshop). Kiro converts the workspace agents to universal V2+V3 JSON and creates backup files (so your original V2 JSON is preserved if you need to compare or revert). Do not select unrelated global agents.

Exit and validate your agent again using the command from step 3.

> **Why this step is not optional:** a V2 JSON agent can be discovered and loaded by the installed CLI, but V3 capability restrictions are not reliably enforced until this conversion runs. In other words, without this step your `deniedCommands` and `deniedPaths` might not actually block anything under V3. Complete the conversion before testing permissions in the next section.

## 5. Run and verify the agent

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Ask:

```text
Explain why APP01 and DATA01 need different cutover designs. Cite the repository
files that support the answer and mark anything unverified.
```

Run `/tools`; the agent should expose read, write, and shell categories. Now test the converted permissions using harmless operations — each test below pairs an action that should succeed with one that should fail, so you can directly observe the restrictions working rather than assuming they do.

**Allowed write:**

```text
Create results/participant/agent-permission-test.md containing: allowed write test
```

The file should be created — `results/participant/**` is on the write allowlist.

**Denied write:**

```text
Create results/blocked/agent-permission-test.md containing: this must be blocked
```

The write must fail because `results/blocked/**` is explicitly denied. This is what proves the write restriction is real, not just documentation.

**Allowed shell:**

```text
Run git status.
```

The command should run because it is allowlisted.

**Denied shell:**

```text
Run rm -rf results/participant/agent-permission-test.md.
```

The command must fail because `rm -rf *` is explicitly denied — this is a deliberately destructive-looking example so you can see the deny-list actually stop a dangerous pattern, not just a harmless placeholder. It targets a throwaway test file you created earlier in this module (not anything important), so even in the unlikely case the deny rule failed to trigger, nothing of value would be lost.

## 6. Understand the controls

| Control | Purpose |
|---|---|
| `tools` | Capabilities the agent can request |
| `allowedTools` | V2 tools trusted without a general approval prompt |
| `toolsSettings` | Portable V2 path and command restrictions |
| `permissions.rules` | V3 allow/ask/deny rules added by `/upgrade-agent` |
| Hooks | Custom pre/post tool logic; added in Module 05 |
| IAM | Final authorization boundary for AWS API calls |

For V3 permission effects, `deny` is more restrictive than `ask`, and `ask` is more restrictive than `allow` — think of it as a strict hierarchy: a `deny` rule always wins even if another rule would allow the same action, and `ask` always pauses for your confirmation even if the agent is otherwise trusted. Do not use `--trust-all-tools` in this workshop, since that flag bypasses all of these checks and defeats the purpose of building a restricted agent.

## 7. Compare with the supplied reference agents

After conversion, inspect:

- `.kiro/agents/windows-upgrade.json` — orchestrator
- `.kiro/agents/upgrade-reviewer.json` — read-only independent auditor
- `.kiro/agents/upgrade-executor.json` — restricted routine executor

The references demonstrate separation of duties: one agent plans and coordinates, one only reviews without the ability to change anything, and one only executes a narrow set of approved scripts. This mirrors how you'd divide responsibilities among people on a real operations team. Your own agent does not need to match them exactly — you'll build your own versions of these specialized roles in Module 10B.

> **Windows users:** the reference agents include both `python3` and `py -3` variants for permitted Python commands.

**Checkpoint:** the manual steering file loads on demand; `my-windows-upgrade` validates and is discovered; `/upgrade-agent` converts the workspace agents; the allowed write and `git status` succeed; the denied write and `rm -rf` fail.
