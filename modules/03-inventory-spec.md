# Module 03 – Inventory with Kiro Spec mode

## Learning objective
Use the v3 Spec chat mode to review requirements, design, and tasks before collecting read-only inventory from APP01 and DATA01.

## Why this matters

Before you upgrade anything, you need an accurate, evidence-based picture of what's actually running on each server — not assumptions. This module introduces Kiro's Spec mode, which is a structured way of turning a goal ("collect inventory") into reviewable requirements, a design, and a task list *before* any code runs. You'll first use Spec mode to understand an existing inventory Spec, then practice creating your own, and finally run the deterministic inventory script and have Kiro help you spot discrepancies against what was assumed. The point is: Spec mode is for planning and review, the Python script is what actually touches AWS and produces evidence.

## 1. Start Kiro in Spec mode

Use the agent you created in Module 02:

```text
kiro-cli chat --v3 --mode spec --agent my-windows-upgrade
```

This selects the v3 engine, your custom agent (so the same restricted permissions from Module 02 apply here too), and structured Spec mode, which breaks a task into requirements → design → tasks instead of jumping straight to execution.

## 2. Review the instructor-approved Spec

At the Kiro prompt, enter:

```text
Review the existing inventory-assessment Spec under .kiro/specs/.
Explain its requirements, design, tasks, outputs, safety boundaries,
and completion evidence in plain language.
Do not edit files and do not call AWS.
```

The repository already contains:

```text
.kiro/specs/inventory-assessment/requirements.md
.kiro/specs/inventory-assessment/design.md
.kiro/specs/inventory-assessment/tasks.md
```

This shows that Kiro can help you understand existing project artifacts — it reads structured documents and explains their purpose, scope, and relationships in plain language, so you don't have to parse them yourself.

To practice creating another Spec, remain in Spec mode and ask:

```text
Create a new Spec named participant-inventory. It must collect read-only
AWS and Windows facts for APP01 and DATA01 through SSM, redact secrets,
identify unsupported Windows roles, and write normalized JSON with
per-server errors. Stop after drafting requirements, design, and tasks;
do not execute the tasks.
```

Review generated files before allowing any execution — Spec mode is designed so you can read and adjust the plan (what will be collected, how, and where it's saved) before a single AWS call happens.

This shows that Kiro can help you break down a complex task into structured requirements, design decisions, and actionable steps — you describe the goal, and it produces a plan you can review before anything runs.

## 3. Collect measured inventory

Exit Kiro, then run the deterministic inventory script. This is a plain Python script, not Kiro — it's the actual mechanism that connects to AWS Systems Manager and pulls real facts from APP01 and DATA01, so the evidence you get doesn't depend on model behavior.

**Windows PowerShell:**

```powershell
py -3 scripts\01_collect_inventory.py `
  --region us-east-1 `
  --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/01_collect_inventory.py \
  --region us-east-1 \
  --stack-name kiro-ws2025-lab
```

## 4. Review the saved evidence

The script wrote its findings to `results/inventory/inventory.json`. Open it to see the raw measured facts before asking Kiro to interpret them:

**Windows PowerShell:**

```powershell
Get-Content results\inventory\inventory.json -Raw |
  ConvertFrom-Json | ConvertTo-Json -Depth 20
```

**Linux/macOS Bash:**

```bash
python3 -m json.tool results/inventory/inventory.json | less
```

Start your normal custom agent again:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Ask:

```text
Compare results/inventory/inventory.json with inventory/assumed-inventory.yaml.
List discrepancies, unknown dependencies, stateful components, unsupported
roles, and missing test oracles. Do not modify either file and do not call AWS.
```

`assumed-inventory.yaml` represents what someone *thought* was running before anyone measured it — comparing it against the real, measured JSON is exactly the kind of assumption-versus-reality check you'd do before any real upgrade project. Program and service discovery is evidence, not proof of ownership or vendor support. Unknowns remain unknown until an application owner resolves them.

This shows that Kiro can help you compare data sets and find discrepancies — it reads JSON/YAML, cross-references fields, and highlights what doesn't match, what's missing, and what needs human decision.

## Transfer to your environment

- **Lab exercise:** `01_collect_inventory.py` knows the workshop stack, two server roles, and where to save normalized evidence.
- **Reusable pattern:** define inventory requirements and acceptance criteria first; collect measured OS, role, service, dependency, identity, storage, and network facts; preserve per-server errors; keep secrets out; treat assumptions as unverified.
- **Adapt before reuse:** replace APP01/DATA01 and stack discovery with your CMDB, tags, account/region scope, owner questionnaire, approved remote-access method, evidence schema, retention policy, and redaction rules.

Adaptation prompt:

```text
Using my manual participant environment profile, draft inventory acceptance
criteria for one real server. Keep missing owners, dependencies, RTO/RPO,
vendor support, and test oracles as UNKNOWN. Do not reuse lab ports or services.
```

**Checkpoint:** both lab servers were collected successfully; services and ports match the lab; no secret values are present; and the participant can explain how Spec mode differs from script execution.
