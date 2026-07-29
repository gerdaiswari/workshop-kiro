# Clone-upgrade requirements

## Objective
Produce Windows Server 2025 AMIs through the AWS-owned clone-upgrade runbook while retaining source servers and recovery evidence.

## Acceptance criteria

- Compatibility report has no blockers and baseline tests pass.
- DATA01 native SQL Server, MySQL, and PostgreSQL backups complete before AMI creation.
- Display exact source instance, subnet, instance profile, target version, expected duration/cost, and rollback before asking for approval.
- Start only after explicit human approval; default to one server at a time.
- Use `TargetWindowsVersion=2025`, `KeepPreUpgradeImageBackUp=True`, and `RebootInstanceBeforeTakingImage=False`.
- Record execution ID, status, runbook outputs, pre-upgrade AMI, upgraded AMI, start/end times, and errors under `results/upgrades/`.
- Do not stop, replace, terminate, or retag source instances.
- Do not call the DATA01 upgraded AMI synchronized or cutover-ready.
