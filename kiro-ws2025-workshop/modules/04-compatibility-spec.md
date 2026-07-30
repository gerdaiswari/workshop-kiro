# Module 04 – Compatibility assessment

## Learning objective
Run deterministic compatibility rules, then use Kiro for evidence-based reasoning and an independent read-only review.

## 1. Run deterministic rules

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

Read `results/compatibility/report.md` and `results/compatibility/report.json`.

## 2. Use Kiro for reasoning, not rule substitution

Start the workshop agent.

**Windows:** `kiro-cli chat --v3 --agent windows-upgrade-windows`

**Linux/macOS:** `kiro-cli chat --v3 --agent windows-upgrade`

Ask:

```text
Activate the windows-upgrade skill. Review the compatibility report.
Separate AWS runbook eligibility, operating-system compatibility, vendor
support unknowns, application test coverage, and production cutover readiness.
Cite evidence paths. Do not modify files and do not call AWS account APIs.
```

Then ask it to use the configured AWS Knowledge MCP server:

```text
Using AWS Knowledge MCP, verify the currently documented supported path and
prerequisites for AWSEC2-CloneInstanceAndUpgradeWindows from Windows Server
2019 to 2025. Compare them with our report and identify drift. Do not call AWS
account APIs and do not edit files.
```

The analyzer should classify DATA01 as eligible for clone compatibility testing but not for AMI-only production cutover.

## 3. Run an independent review

Exit the first chat and start the read-only reviewer:

```text
kiro-cli chat --v3 --agent upgrade-reviewer
```

Ask:

```text
Challenge results/compatibility/report.md for false passes, unknown vendor
support, database consistency risks, and missing rollback evidence.
Return findings only; do not edit files or call AWS.
```

**Checkpoint:** no unresolved AWS prerequisite blocker exists, every workload has a test oracle, and stateful cutover remains blocked by design.
