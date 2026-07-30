# Clone-upgrade tasks

- [ ] 1. Verify eligibility report, baseline evidence, source IDs, and recovery plan.
- [ ] 2. Run and verify DATA01 native backups; do not commit backup files.
- [ ] 3. Present APP01 runbook command, cost/time, and rollback; obtain explicit approval.
- [ ] 4. Run `python3 scripts/04_start_upgrade.py --server APP01 ...` and monitor to terminal state.
- [ ] 5. Record APP01 upgraded and retained pre-upgrade AMI IDs.
- [ ] 6. Separately present DATA01 change; obtain explicit approval.
- [ ] 7. Run DATA01 upgrade and record outputs.
- [ ] 8. Confirm both source instances remain healthy and still report Windows Server 2019.

> Do not execute clone-upgrade tasks in unattended chat with broad tool trust. Review each mutation and keep typed confirmation enabled.
