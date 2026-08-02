# Module 10B – Create specialized agents, choose models, and use subagents

## Learning objective

Create your own reviewer and executor agents, assign models that are actually available to your account, validate their schemas, and let your main agent delegate a read-only review through subagents.

## Why this matters

So far you've built one agent that does everything: reads, writes, runs shell commands. In Module 02 you saw the reference `windows-upgrade`, `upgrade-reviewer`, and `upgrade-executor` agents and how they split responsibilities — this module has you build your own versions of that split. The idea is: a reviewer agent should only be able to read and challenge (never fix, so it can't paper over its own findings), and an executor agent should only be able to run a short list of approved scripts (never make judgment calls). You'll also see "subagents" in action — your main agent delegating a task to these specialized agents and combining their outputs into one report, rather than doing everything itself in one undifferentiated session.

> **Workshop navigation:** Module 06 upgrades are running → Module 09 → Module 10 → **Module 10B (you are here)** → return to Module 07 only after both upgrades succeed.
>
> This is the final learning activity during the upgrade wait. When finished, check both upgrade terminals; Module 07 requires `Success` and upgraded AMI IDs for both servers.

## 1. Discover models before configuring them

Model availability and credit multipliers can change by account, so don't hardcode a model ID from memory or from this document — check what's actually available to you right now:

```text
kiro-cli chat --list-models
```

Machine-readable output:

```text
kiro-cli chat --list-models --format json-pretty
```

Choose:

- One higher-capability model for architecture and independent review — reviewing evidence for blockers and unsupported assumptions benefits from stronger reasoning.
- One lower-cost model for deterministic, routine inspection — running a script and reporting its output doesn't need the most expensive model available.

At the time this repository was validated, `claude-sonnet-5` and `claude-haiku-4.5` were available. Use them only if they appear in your own output — availability varies by account, so don't assume these exact names will work for you.

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
    "@aws-knowledge-mcp-server/*"
  ],
  "allowedTools": [
    "read",
    "grep",
    "glob",
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

The reviewer intentionally has no `write`, `shell`, or authenticated AWS operation tool — this is the whole point of the role: it can look at evidence and reason about it, but it physically cannot change anything, so its findings are trustworthy precisely because it has no way to alter what it's reviewing.

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

This executor can run only the listed local checks. It cannot call AWS — its `deniedCommands` list explicitly blocks any `aws *` command, so even if you ask it to, it structurally cannot make an AWS API call. This makes it safe to run routine checks with, without worrying about scope creep.

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

If validation reports an unavailable model, return to `--list-models`, use an exact ID (copy it exactly, since a typo or a deprecated name will fail validation), and validate again.

The two files were created with V2 portability fields. Convert only the newly listed V2 workspace agents before testing their V3 tool boundaries — this is the same `/upgrade-agent` conversion step from Module 02, now applied to these two new agent files:

```text
kiro-cli chat --v3
```

Run `/upgrade-agent`, select **V2 Workspace**, and confirm the listed agents are `participant-reviewer` and `participant-executor`. Exit and validate both files again.

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

Notice that tool boundaries—not only the prompt—separate their responsibilities. Both agents could technically be asked to do the other's job in plain English, but the reviewer's missing `write`/`shell` tools and the executor's `deniedCommands` list mean the request would simply fail, regardless of how it's phrased. That's a much stronger guarantee than relying on the model to just follow instructions.

This shows that Kiro can help you split complex work into specialized roles — a reviewer that only reads and challenges, an executor that only runs approved checks — so each agent does one job well with the minimum permissions needed.

## 6. Enable subagents on your main agent

A subagent is a way for one Kiro agent (your orchestrator, `my-windows-upgrade`) to delegate part of a task to another named agent and get its output back — instead of you manually switching between `participant-reviewer` and `participant-executor` yourself, your main agent can coordinate both of them in a single request. Enable Kiro's documented subagent setting:

```text
kiro-cli settings chat.enableSubagent true
```

Use plain Kiro to update `.kiro/agents/my-windows-upgrade.json`:

1. Add `"subagent"` to `tools` — this is the capability that lets the agent delegate to other named agents at all.
2. Do not add it to `allowedTools` — this means every delegation attempt still needs your approval rather than happening silently.
3. Add a V3 permission rule with capability `subagent` and effect `ask`.

This makes every delegation request visible for participant approval, so you always see when your main agent hands work off to the reviewer or executor, and to which one.

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

Subagents improve separation of duties but do not remove human approval or IAM boundaries — delegating to a stricter agent doesn't grant it any more permission than its own JSON file allows, and you still approve the delegation itself because of the `ask` effect you just configured.

This shows that Kiro can help you orchestrate multi-step workflows — your main agent delegates tasks to specialists (run checks → review results), combines their outputs into one report, and you stay in control of what each agent is allowed to do.

## 7. Compare with the supplied multi-agent design

After your pipeline works, compare it with the reference agents:

- `.kiro/agents/windows-upgrade.json` — orchestrator with full tools, subagent, and MCP
- `.kiro/agents/upgrade-executor.json` — restricted to scripts, cheap model, no MCP
- `.kiro/agents/upgrade-reviewer.json` — read-only auditor, strong model, has MCP

This is the **trust boundary model**: the orchestrator plans and coordinates, the executor runs approved tasks with minimum permissions, and the reviewer audits independently without the ability to fix. The orchestrator absorbs planning because a separate planner would not add another trust boundary; it uses the account's selected/default model unless you explicitly add a `model` field.

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
