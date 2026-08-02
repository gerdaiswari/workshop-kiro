# Module 02 – Create steering, an agent, and tool permissions

## Learning objective

Create workspace steering and a restricted custom agent, convert the agent once for Kiro CLI V3, and verify its allowed and denied operations with harmless tests.

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

Steering gives Kiro durable instructions and context:

- **Global steering** lives in `~/.kiro/steering/` and applies across workspaces.
- **Workspace steering** lives in `.kiro/steering/` and applies only to this repository.
- `inclusion: always` loads a file automatically.
- `inclusion: manual` loads a file only when you add it with `/context add`.

Run `/context show`. The supplied `.kiro/steering/safety-rules.md` is the always-loaded example.

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

Confirm and load the manual file:

```text
/context show
/context add .kiro/steering/participant-environment.md
/context show
```

The first `/context show` should omit the manual file; the second should include it.

## 3. Create the restricted custom agent

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

Exit Kiro and validate from the repository root.

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

Do not continue until validation succeeds and `my-windows-upgrade` appears as a workspace agent.

## 4. Convert workspace agents for V3

The JSON created above uses the portable V2 fields (`allowedTools` and `toolsSettings`). Convert the workspace agents once so the V3 trust engine receives equivalent `permissions.rules`:

```text
kiro-cli chat --v3
```

Inside chat, run:

```text
/upgrade-agent
```

Select **V2 Workspace**. Kiro converts the workspace agents to universal V2+V3 JSON and creates backup files. Do not select unrelated global agents.

Exit and validate the participant agent again using the command from step 3.

> A V2 JSON agent can be discovered and loaded by the installed CLI, but V3 capability restrictions are not reliably enforced until this conversion. Complete the conversion before testing permissions.

## 5. Run and verify the agent

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Ask:

```text
Explain why APP01 and DATA01 need different cutover designs. Cite the repository
files that support the answer and mark anything unverified.
```

Run `/tools`; the agent should expose read, write, and shell categories. Now test the converted permissions using harmless operations.

**Allowed write:**

```text
Create results/participant/agent-permission-test.md containing: allowed write test
```

The file should be created.

**Denied write:**

```text
Create results/blocked/agent-permission-test.md containing: this must be blocked
```

The write must fail because `results/blocked/**` is explicitly denied.

**Allowed shell:**

```text
Run git status.
```

The command should run because it is allowlisted.

**Denied shell:**

```text
Run echo blocked-test.
```

The command must fail because that exact harmless command is explicitly denied.

## 6. Understand the controls

| Control | Purpose |
|---|---|
| `tools` | Capabilities the agent can request |
| `allowedTools` | V2 tools trusted without a general approval prompt |
| `toolsSettings` | Portable V2 path and command restrictions |
| `permissions.rules` | V3 allow/ask/deny rules added by `/upgrade-agent` |
| Hooks | Custom pre/post tool logic; added in Module 05 |
| IAM | Final authorization boundary for AWS API calls |

For V3 permission effects, `deny` is more restrictive than `ask`, and `ask` is more restrictive than `allow`. Do not use `--trust-all-tools` in this workshop.

## 7. Compare with the supplied reference agents

After conversion, inspect:

- `.kiro/agents/windows-upgrade.json` — orchestrator
- `.kiro/agents/upgrade-reviewer.json` — read-only independent auditor
- `.kiro/agents/upgrade-executor.json` — restricted routine executor

The references demonstrate separation of duties. Your participant agent does not need to match them exactly.

> **Windows users:** the reference agents include both `python3` and `py -3` variants for permitted Python commands.

**Checkpoint:** the manual steering file loads on demand; `my-windows-upgrade` validates and is discovered; `/upgrade-agent` converts the workspace agents; the allowed write and `git status` succeed; the denied write and `echo blocked-test` fail.
