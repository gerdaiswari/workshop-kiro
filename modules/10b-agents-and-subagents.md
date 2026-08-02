# Module 10B – Create specialized agents, choose models, and use subagents

## Learning objective

Create your own reviewer and executor agents, assign models that are actually available to your account, validate their schemas, and let your main agent delegate a read-only review through subagents.

> **Workshop navigation:** Module 06 upgrades are running → Module 09 → Module 10 → **Module 10B (you are here)** → return to Module 07 only after both upgrades succeed.
>
> This is the final learning activity during the upgrade wait. When finished, check both upgrade terminals; Module 07 requires `Success` and upgraded AMI IDs for both servers.

## 1. Discover models before configuring them

Model availability and credit multipliers can change by account. List the models available now:

```text
kiro-cli chat --list-models
```

Machine-readable output:

```text
kiro-cli chat --list-models --format json-pretty
```

Choose:

- One higher-capability model for architecture and independent review.
- One lower-cost model for deterministic, routine inspection.

At the time this repository was validated, `claude-sonnet-5` and `claude-haiku-4.5` were available. Use them only if they appear in your own output.

## 2. Create a read-only reviewer agent

Start plain Kiro:

```text
kiro-cli chat --v3
```

Ask it to create `.kiro/agents/participant-reviewer.json` with the following configuration. Replace `AVAILABLE_REVIEW_MODEL` with the exact higher-capability model ID you selected before approving the write.

```json
{
  "name": "participant-reviewer",
  "description": "Participant-created independent reviewer for Windows upgrade evidence.",
  "model": "AVAILABLE_REVIEW_MODEL",
  "prompt": "Act as an independent reviewer. Inspect existing evidence, identify blockers and unsupported assumptions, and never repair or mutate the system you are reviewing.",
  "tools": [
    "read",
    "grep",
    "glob",
    "code",
    "@aws-knowledge-mcp-server/*"
  ],
  "allowedTools": [
    "read",
    "grep",
    "glob",
    "code",
    "@aws-knowledge-mcp-server/*"
  ],
  "mcpServers": {
    "aws-knowledge-mcp-server": {
      "url": "https://knowledge-mcp.global.api.aws",
      "timeout": 120000
    }
  },
  "resources": [
    "file://README.md",
    "file://.kiro/steering/**/*.md",
    "skill://.kiro/skills/**/SKILL.md"
  ]
}
```

The reviewer intentionally has no `write`, `shell`, or authenticated AWS operation tool.

## 3. Create a routine executor agent

Ask plain Kiro to create `.kiro/agents/participant-executor.json`. Replace `AVAILABLE_EXECUTION_MODEL` with the exact lower-cost model ID you selected.

```json
{
  "name": "participant-executor",
  "description": "Participant-created agent for routine local validation tasks.",
  "model": "AVAILABLE_EXECUTION_MODEL",
  "prompt": "Run one deterministic, approved local task at a time. Show the command, capture the result, and escalate architecture or risk decisions to a reviewer.",
  "tools": [
    "read",
    "grep",
    "glob",
    "shell"
  ],
  "allowedTools": [
    "read",
    "grep",
    "glob"
  ],
  "toolsSettings": {
    "shell": {
      "allowedCommands": [
        "python3 tests/static/validate_repo.py*",
        "py -3 tests/static/validate_repo.py*",
        "git status*",
        "git diff*"
      ],
      "deniedCommands": [
        "aws *",
        "rm -rf *",
        "Remove-Item * -Recurse*"
      ],
      "autoAllowReadonly": true,
      "denyByDefault": true
    }
  },
  "resources": [
    "file://README.md",
    "file://.kiro/steering/**/*.md"
  ]
}
```

This executor can run only the listed local checks. It cannot call AWS.

## 4. Validate the agents you created

**Windows PowerShell:**

```powershell
kiro-cli agent validate --path .kiro\agents\participant-reviewer.json
kiro-cli agent validate --path .kiro\agents\participant-executor.json
kiro-cli agent list
```

**Linux/macOS Bash:**

```bash
kiro-cli agent validate --path .kiro/agents/participant-reviewer.json
kiro-cli agent validate --path .kiro/agents/participant-executor.json
kiro-cli agent list
```

If validation reports an unavailable model, return to `--list-models`, use an exact ID, and validate again.

## 5. Use each specialized agent directly

Start the reviewer:

```text
kiro-cli chat --v3 --agent participant-reviewer
```

Ask:

```text
Review existing baseline, backup, compatibility, and post-upgrade evidence.
Report blockers, warnings, missing tests, and unsupported assumptions.
Do not edit files and do not call AWS account APIs.
```

Then start the executor:

```text
kiro-cli chat --v3 --agent participant-executor
```

Ask:

```text
Run the repository quick validator and summarize only its deterministic output.
Show the command before running it.
```

Notice that tool boundaries—not only the prompt—separate their responsibilities.

This shows that Kiro can help you split complex work into specialized roles — a reviewer that only reads and challenges, an executor that only runs approved checks — so each agent does one job well with the minimum permissions needed.

## 6. Enable subagents on your main agent

Enable Kiro's documented subagent setting:

```text
kiro-cli settings chat.enableSubagent true
```

Use plain Kiro to add `"subagent"` to the `tools` array in `.kiro/agents/my-windows-upgrade.json`. Do not add it to `allowedTools`; review delegation requests before approval.

Validate `my-windows-upgrade.json` again, then restart it:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Ask:

```text
Use participant-executor and participant-reviewer as subagents for a read-only
review. The executor may run only the quick local validator. The reviewer must
independently inspect the resulting evidence and identify gaps. Return one
combined report. Do not call AWS and do not modify files.
```

Subagents improve separation of duties but do not remove human approval or IAM boundaries.

This shows that Kiro can help you orchestrate multi-step workflows — your main agent delegates tasks to specialists (run checks → review results), combines their outputs into one report, and you stay in control of what each agent is allowed to do.

## 7. Compare with the supplied multi-agent design

After your pipeline works, compare it with the reference agents:

- `.kiro/agents/windows-upgrade.json` — orchestrator with full tools, subagent, and MCP
- `.kiro/agents/upgrade-executor.json` — restricted to scripts, cheap model, no MCP
- `.kiro/agents/upgrade-reviewer.json` — read-only auditor, strong model, has MCP

This is the **trust boundary model**: orchestrator plans and coordinates, executor runs approved tasks with minimum permissions, reviewer audits independently without the ability to fix. The orchestrator absorbed the planner role because both need the same strong model and read access — a separate planner adds no trust boundary.

Look for differences in models, tools, MCP access, shell boundaries, resources, and role prompts. The supplied agents are reference implementations you can now evaluate rather than unexplained files.

## 8. Understand the controls

| Field or setting | Function |
|---|---|
| `model` | Exact model ID discovered with `--list-models` |
| `prompt` | Specialized responsibility and behavior |
| `tools` | Capabilities the agent may request |
| `allowedTools` | Capabilities trusted without prompting |
| `toolsSettings` | Command, path, or AWS-service restrictions |
| `resources` | Steering and skills loaded into context |
| `mcpServers` | External MCP connections owned by the agent |
| `chat.enableSubagent` | Enables delegation through the subagent tool |

A lower-cost model can reduce usage cost but may produce different quality. Use deterministic scripts for execution and stronger independent review for risk decisions.

**Checkpoint:** you selected currently available model IDs, created and validated two specialized agents, ran each directly, added the subagent tool to your main agent, and completed a read-only delegated review.
