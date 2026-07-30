# Module 10B – Custom agents, subagents, and model selection

## Learning objective
Use verified Kiro CLI commands to select specialized agents and models, and understand when a lower-cost model or lower reasoning effort is appropriate.

## 1. Check the models available to your account

Model availability can change and can differ by account. Never copy a model ID without checking it first.

```text
kiro-cli chat --list-models
```

For machine-readable output:

```text
kiro-cli chat --list-models --format json-pretty
```

The workshop preflight verifies that every model configured in `.kiro/agents/` appears in this list:

**Windows:**

```powershell
py -3 scripts\check_kiro_prereqs.py
```

**Linux/macOS:**

```bash
python3 scripts/check_kiro_prereqs.py
```

At the time this repository was validated, the workshop agents used:

| Agent | Configured model | Purpose |
|---|---|---|
| `windows-upgrade` | Account default | General workshop work on Linux/macOS |
| `windows-upgrade-windows` | Account default | General workshop work on Windows |
| `upgrade-planner` | `claude-sonnet-5` | Planning and risk analysis |
| `upgrade-executor` | `claude-haiku-4.5` | Routine scripted work |
| `upgrade-reviewer` | `claude-sonnet-5` | Independent evidence review |

If the preflight reports an unavailable model, choose an ID shown by `--list-models`, update the relevant agent JSON, and validate again. Kiro's agent configuration documentation states that an unavailable agent model falls back to the default, but the workshop preflight treats that as an error so the change is visible.

## 2. Validate and list the custom agents

```text
kiro-cli agent validate --path .kiro/agents/upgrade-planner.json
kiro-cli agent validate --path .kiro/agents/upgrade-executor.json
kiro-cli agent validate --path .kiro/agents/upgrade-reviewer.json
kiro-cli agent list
```

Run these commands from the repository root. Workspace agents are discovered from `.kiro/agents/`.

## 3. Use the planner for complex reasoning

```text
kiro-cli chat --v3 --agent upgrade-planner
```

Ask:

```text
Given the APP01 and DATA01 inventory, design a wave-based upgrade strategy
for 40 similar servers. Include risk tiers, gate criteria, rollback boundaries,
and the evidence required before each wave. Do not modify files or call AWS.
```

The planner has read-only tools and a stronger configured model.

## 4. Use the executor for routine work

```text
kiro-cli chat --v3 --agent upgrade-executor
```

Ask it to run one deterministic task at a time, for example:

```text
Run the repository's read-only inventory collection script for us-east-1
and summarize the saved result. Show the command before executing it.
```

The executor has restricted write paths and shell commands. Its model is chosen for lower-cost routine work, not for architecture approval.

For a one-off simple request, Kiro also supports a lower reasoning-effort option:

```text
kiro-cli chat --v3 --effort low --agent upgrade-executor
```

## 5. Use the reviewer independently

```text
kiro-cli chat --v3 --agent upgrade-reviewer
```

Ask:

```text
Review the evidence under results/ and the compatibility report.
Report blockers, warnings, untested services, and unsupported assumptions.
Do not edit files and do not call AWS.
```

The reviewer is intentionally read-only. It should identify gaps rather than silently repair them.

## 6. Enable and exercise subagents

Kiro CLI exposes a documented subagent setting. Enable it once:

```text
kiro-cli settings chat.enableSubagent true
```

Restart the chat after changing settings, then start the main agent for your workstation.

**Windows:** `kiro-cli chat --v3 --agent windows-upgrade-windows`

**Linux/macOS:** `kiro-cli chat --v3 --agent windows-upgrade`

Ask:

```text
Use subagents to create a three-stage, read-only review:
1. The planner proposes post-upgrade test coverage.
2. The executor inspects existing test result files only; do not run mutations.
3. The reviewer identifies evidence gaps.
Return one combined report and make no AWS changes.
```

The calling agent must include `subagent` in its `tools` list; both workstation-specific main agent files do.

## 7. Understand the configuration fields

| Field | Meaning |
|---|---|
| `model` | Model ID from `kiro-cli chat --list-models` |
| `tools` | Tools the agent may request |
| `allowedTools` | Tools automatically approved without prompting |
| `toolsSettings` | Restrictions for paths, commands, and services |
| `resources` | Files and skills loaded into context |
| `hooks` | Commands run at documented agent/tool lifecycle triggers |
| `prompt` | Role, behavior, and safety instructions |

## Important limitations

- Model availability and credit multipliers can change; always run `--list-models` and the preflight.
- A cheaper model can reduce usage cost, but it may produce different quality. Always review evidence and decisions.
- `--trust-all-tools` bypasses approval prompts; do not use it for this workshop.
- Custom-agent restrictions and hooks are defense in depth. IAM remains authoritative for AWS access.
- Subagents do not remove the need for human review or mutation approval.

**Checkpoint:** all custom agents validate, configured models pass the preflight, at least two agents have been used, and the participant can explain why routine execution and architecture decisions use different controls.
