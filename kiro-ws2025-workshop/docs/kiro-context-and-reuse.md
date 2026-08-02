# Kiro context and reuse guide

Use this page before starting the hands-on modules. It explains why the repository contains many Kiro files, what is actually loaded into a chat, and how to reuse the workshop without assuming that every Windows workload looks like APP01 or DATA01.

## The short answer: the repository will not load every file into every prompt

Running Kiro from the repository root makes the workspace **discoverable**. It does not copy every module, script, Spec, agent, and application file into each turn.

Kiro context has four useful states:

| State | Meaning in this workshop | Examples |
|---|---|---|
| **Always loaded** | Short rules that should affect every workspace conversation | `.kiro/steering/safety-rules.md` |
| **Selected with an agent** | Role, tools, trust rules, and explicitly declared resources for the named agent | `.kiro/agents/my-windows-upgrade.json` or a supplied reference agent |
| **Activated when relevant** | Detailed reusable procedure or reference material | `.kiro/skills/windows-upgrade/` |
| **Discoverable and read when requested** | Files Kiro can inspect with tools, but whose full contents do not need to be permanent context | `.kiro/specs/`, `modules/`, `scripts/`, `apps/`, `inventory/`, and `results/` |

## Inspect context instead of guessing

At the start of a chat, run:

```text
/context show
```

Check which steering and resource files are present. If a manual steering file is needed for the current task, add it deliberately with `/context add`, then run `/context show` again.

Also use these views when relevant:

```text
/tools
/hooks
```

`/tools` shows what the current agent can request. `/hooks` shows hooks attached to that agent. Context, tools, trust, and hooks are different controls.

## Use focused sessions

Start a fresh chat for a new phase instead of carrying one long conversation through the entire workshop. Do not use `--resume` unless you intentionally want the previous conversation history.

Begin each task with four boundaries:

```text
Goal: <one outcome>
Evidence to read: <specific files or directories>
Allowed actions: <read-only, local write, or approved AWS phase>
Stop condition: <what must be true before continuing>
```

Example:

```text
Goal: assess one server's upgrade readiness.
Evidence to read: its measured inventory and baseline test results.
Allowed actions: read only; do not call AWS or edit files.
Stop condition: report pass, warning, unknown, or blocker with evidence paths.
```

This is more reliable than asking Kiro to "review everything."

## Read every module in two lanes

Each workflow module separates two concerns:

1. **Lab lane** — exact APP01/DATA01 commands that make the classroom environment reproducible.
2. **Transfer lane** — the reusable decision pattern and questions to adapt for a real workload.

Do not copy lab values into a production environment. Replace at least:

- account, region, subnet, IAM role/profile, tags, and instance IDs;
- source/target Windows versions and exact runbook schema;
- server roles, application owners, dependencies, identities, and vendor support;
- RTO, RPO, maintenance windows, backup/restore design, and cutover ownership;
- service checks with business transactions and data reconciliation for that workload.

Unknown values remain `UNKNOWN`; APP01 or DATA01 defaults must never fill missing production facts.

## What to reuse in your own repository

Start small. A real workload repository does not need every file in this lab.

| Need | Reuse or create |
|---|---|
| Rules that must apply to every task | A short always-loaded steering file |
| Environment-specific facts | Inventory/evidence files, or manual steering if truly needed across several turns |
| A specialist role and tool boundary | One custom agent with only required tools/resources |
| A repeatable Windows upgrade method | The `windows-upgrade` skill, adapted without lab IDs |
| A high-impact change plan | A Spec with requirements, design, tasks, gates, and evidence |
| Deterministic pass/fail | Scripts and tests owned by the workload team |
| Current AWS documentation | A reviewed read-only documentation MCP integration |

Recommended minimum structure:

```text
.kiro/
  steering/safety.md
  agents/windows-upgrade.json
  skills/windows-upgrade/SKILL.md
  specs/<current-change>/
inventory/
tests/
results/
```

Copy a reference file only after you can explain its purpose. Remove lab names, fixed ports, stack names, and synthetic test expectations.

## Reusable upgrade lifecycle

The portable lifecycle demonstrated by the lab is:

1. discover measured facts and owners;
2. classify state, identity, dependencies, and unsupported roles;
3. verify AWS eligibility separately from application/vendor compatibility;
4. define deterministic baseline and recovery evidence;
5. clone-upgrade after approval;
6. validate an isolated copy;
7. compare evidence and block unexplained regressions;
8. design cutover and rollback according to state and RTO/RPO;
9. roll out in controlled waves;
10. clean up only after separate approval and retention checks.

Kiro assists with discovery, planning, code analysis, evidence review, and orchestration. AWS Systems Manager performs the OS upgrade. Workload-owned tests and human approvals decide whether the result can progress.
