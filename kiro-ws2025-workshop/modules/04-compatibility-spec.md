# Module 04 – Compatibility assessment

## Run deterministic rules

```bash
python3 scripts/02_analyze_compatibility.py \
  --inventory results/inventory/inventory.json \
  --output-dir results/compatibility
```

Read `results/compatibility/report.md` and `report.json`.

## Use Kiro for reasoning, not rule substitution

In Kiro:

```text
Activate the windows-upgrade skill. Review the compatibility report. Separate: AWS runbook eligibility, operating-system compatibility, vendor support unknowns, application test coverage, and production cutover readiness. Cite evidence paths.
```

Then use the AWS Knowledge MCP server:

```text
Using AWS Knowledge MCP, verify the currently documented supported path and prerequisites for AWSEC2-CloneInstanceAndUpgradeWindows from Windows Server 2019 to 2025. Compare them to our report and identify drift. Do not call AWS account APIs.
```

The sample analyzer should identify DATA01 as eligible for clone testing but not AMI-only live cutover.

## Optional independent review

```text
Delegate an independent reviewer to challenge the report for false passes, unknown vendor support, database consistency, and missing rollback evidence. Return findings only.
```

**Checkpoint:** no AWS prerequisite blocker, every workload has tests, and stateful cutover remains blocked by design.
