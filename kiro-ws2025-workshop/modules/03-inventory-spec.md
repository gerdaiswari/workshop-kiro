# Module 03 – Inventory with Kiro Spec mode

## Learning objective
Use the v3 Spec chat mode to review requirements, design, and tasks before collecting read-only inventory from APP01 and DATA01.

## 1. Start Kiro in Spec mode

Use the agent you created in Module 02:

```text
kiro-cli chat --v3 --mode spec --agent my-windows-upgrade
```

This selects the v3 engine, your custom agent, and structured Spec mode.

## 2. Review the instructor-approved Spec

At the Kiro prompt, enter:

```text
Review the existing inventory-assessment Spec under .kiro/specs/.
Explain its requirements, design, tasks, outputs, safety boundaries,
and completion evidence to a participant who has never used Kiro.
Do not edit files and do not call AWS.
```

The repository already contains:

```text
.kiro/specs/inventory-assessment/requirements.md
.kiro/specs/inventory-assessment/design.md
.kiro/specs/inventory-assessment/tasks.md
```

To practice creating another Spec, remain in Spec mode and ask:

```text
Create a new Spec named participant-inventory. It must collect read-only
AWS and Windows facts for APP01 and DATA01 through SSM, redact secrets,
identify unsupported Windows roles, and write normalized JSON with
per-server errors. Stop after drafting requirements, design, and tasks;
do not execute the tasks.
```

Review generated files before allowing any execution.

## 3. Collect measured inventory

Exit Kiro, then run the deterministic inventory script.

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

Program and service discovery is evidence, not proof of ownership or vendor support. Unknowns remain unknown until an application owner resolves them.

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
