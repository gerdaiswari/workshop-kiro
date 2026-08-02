# Module 04 – Compatibility assessment

## Learning objective
Run deterministic compatibility rules, then use Kiro for evidence-based reasoning and an independent read-only review.

## Why this matters

Knowing what's installed (Module 03) isn't the same as knowing whether it's *safe to upgrade*. This module separates two roles that are easy to blur: a deterministic Python script applies fixed pass/warning/blocker rules against the measured inventory (so the eligibility decision doesn't depend on a model's guess), while Kiro is used afterward to organize, explain, and challenge those results — never to invent facts the script didn't check. You'll also see why DATA01, despite passing eligibility checks, is not ready for a production cutover the way APP01 is.

## 1. Run deterministic rules

This script reads the inventory you collected in Module 03 and applies fixed compatibility rules — no model involved — to classify each finding as pass, warning, unknown, or blocker.

**Windows PowerShell:**

```powershell
py -3 scripts\02_analyze_compatibility.py `
  --inventory results\inventory\inventory.json `
  --output-dir results\compatibility
```

**Linux/macOS Bash:**

```bash
python3 scripts/02_analyze_compatibility.py \
  --inventory results/inventory/inventory.json \
  --output-dir results/compatibility
```

Read `results/compatibility/report.md` and `results/compatibility/report.json`. These files are the source of truth for what's compatible — everything Kiro says next should trace back to lines in these reports.

## 2. Use your agent for reasoning, not rule substitution

Start the agent you created in Module 02:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Ask:

```text
Review the compatibility report. Separate AWS runbook eligibility,
operating-system compatibility, vendor-support unknowns, application test
coverage, and production cutover readiness. Cite evidence paths. Treat any
current-documentation fact we have not verified as unknown. Do not modify files
and do not call AWS account APIs.
```

The deterministic analyzer remains the source of pass/warning/blocker results. Your agent adds structured reasoning but must not invent current AWS or vendor facts — that's why the prompt tells it to mark unverified facts as unknown rather than guessing. Module 09 will add AWS Knowledge MCP for documentation checks, giving Kiro a way to check current AWS facts instead of relying on training data.

This shows that Kiro can help you organize and interpret complex assessment results — it separates concerns (eligibility, compatibility, vendor support, test coverage, cutover readiness) and maps each finding back to evidence files, so you get a structured picture instead of a flat report.

The analyzer should classify DATA01 as eligible for clone compatibility testing but not for AMI-only production cutover — this is intentional. A database keeps accepting writes after its image is captured, so an AMI-based clone is always a snapshot in the past; it's fine to validate against, but not to promote to production as-is. Module 08 explains this distinction in more depth.

## 3. Request a fresh read-only challenge

Exit the custom agent and start a new plain session — deliberately without your custom agent, so this second look isn't anchored on the same conversation history and framing as the first pass:

```text
kiro-cli chat --v3
```

Ask:

```text
Act as a read-only challenger. Review results/compatibility/report.md for false
passes, unknown vendor support, database consistency risks, and missing rollback
evidence. Return findings only; do not edit files or call AWS.
```

This is a simple second pass, not a fully isolated specialist. In Module 10B you will create a dedicated reviewer agent with its own model and restricted tools.

This shows that Kiro can help you challenge your own work — it acts as an independent reviewer that pokes holes in assumptions, finds missing evidence, and identifies risks you might have overlooked.

## Transfer to your environment

- **Lab exercise:** the supplied analyzer evaluates known APP01/DATA01 facts and demonstrates why technical eligibility is not the same as production readiness.
- **Reusable pattern:** evaluate AWS runbook eligibility, Windows compatibility, vendor support, application behavior, data consistency, and cutover readiness as separate decisions with `pass`, `warning`, `unknown`, or `blocker` evidence.
- **Adapt before reuse:** obtain the exact runtime/driver/plugin matrix, unsupported Windows roles, licensing position, owner decision, business test oracle, and current AWS/vendor documentation for each workload. Extend deterministic rules rather than asking a model to invent a pass.

Adaptation prompt:

```text
Challenge my real workload's compatibility evidence. Separate AWS eligibility,
OS support, vendor certification, application test coverage, state consistency,
and cutover readiness. Keep every unverified fact UNKNOWN.
```

**Checkpoint:** no unresolved AWS prerequisite blocker exists for the lab, every lab workload has a test oracle, and stateful cutover remains blocked by design.
