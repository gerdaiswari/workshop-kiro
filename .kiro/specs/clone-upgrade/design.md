# Clone-upgrade design

`04_start_upgrade.py` loads stack outputs, the compatibility report, and the baseline test summary. For DATA01 it reads the existing `results/backups/summary.json` evidence written by `03_run_tests.py --phase backup-data` and aborts unless that backup phase passed. It does not create the backup itself. It prints a change summary and requires a typed logical server name unless `--yes` is supplied by an already approved automation context.

It calls `ssm start-automation-execution` for `AWSEC2-CloneInstanceAndUpgradeWindows` using only parameters exposed by the documented runbook. A polling loop records every status transition. Output values are searched for AMI IDs but the full response remains authoritative.

The runbook creates its own temporary instance and terminates that temporary instance. Workshop cleanup separately handles retained AMIs, snapshots, and validation instances.
