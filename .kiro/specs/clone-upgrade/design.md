# Clone-upgrade design

`04_start_upgrade.py` loads stack outputs, the compatibility report, and the baseline test summary. For DATA01 it reads the existing `results/backups/summary.json` evidence written by `03_run_tests.py --phase backup-data` and aborts unless that backup phase passed. It does not create the backup itself. It prints a change summary and requires a typed logical server name unless `--yes` is supplied by an already approved automation context.

Before approval, it calls `ssm describe-document` for `AWSEC2-CloneInstanceAndUpgradeWindows`, records the regional default document version, and inspects its parameter names. It accepts the documented `TargetWindowsVersion` spelling or the `TargetWindowVersion` spelling currently exposed by AWS document version 46, then pins the inspected document version when calling `ssm start-automation-execution`. If neither spelling exists, the script stops rather than guessing or silently omitting the target version. A polling loop records every status transition. Output values are searched for AMI IDs but the full response remains authoritative.

The runbook creates its own temporary instance and terminates that temporary instance. Workshop cleanup separately handles retained AMIs, snapshots, and validation instances.
