# Clone-upgrade design

`04_start_upgrade.py` loads stack outputs and the compatibility report. For DATA01 it first runs `backup_data01.ps1` through SSM and verifies backup results. It prints a change summary and requires a typed logical server name unless `--yes` is supplied by an already approved automation context.

It calls `ssm start-automation-execution` for `AWSEC2-CloneInstanceAndUpgradeWindows` using only parameters exposed by the documented runbook. A polling loop records every status transition. Output values are searched for AMI IDs but the full response remains authoritative.

The runbook creates its own temporary instance and terminates that temporary instance. Workshop cleanup separately handles retained AMIs, snapshots, and validation instances.
