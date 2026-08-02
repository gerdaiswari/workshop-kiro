---
name: windows-upgrade
description: Evidence-driven workflow for assessing, clone-upgrading, validating, and safely promoting Windows Server EC2 workloads. Use for Windows inventory, compatibility, SSM upgrade planning, test design, rollback, and fleet waves.
---

# Windows EC2 upgrade skill

## Required workflow

1. Discover facts; do not infer workload statefulness from ports alone.
2. Classify each server: stateless, stateful, identity-sensitive, unsupported role, or unknown.
3. Capture owner, RTO/RPO, maintenance allowance, dependencies, vendor support, and test oracle.
4. Verify the exact AWS runbook schema and prerequisites for the source/target versions.
5. Produce baseline inventory, native backups for stateful services, and deterministic tests.
6. Clone-upgrade; never describe this as upgrading production in place.
7. Launch an isolated validation instance from the upgraded AMI.
8. Compare baseline and post evidence. Any unexplained regression blocks promotion.
9. Use blue/green or target switching only for synchronized/stateless tiers.
10. Roll out in small waves and retain recovery artifacts for the agreed period.

## Mandatory outputs

- Inventory JSON and compatibility report.
- Requirements/design/tasks Spec with acceptance criteria.
- Baseline and post-upgrade test JSON.
- Upgrade execution ID, source instance ID, pre-upgrade AMI, upgraded AMI.
- Decision record: pass, conditional pass, blocked, or unsupported.
- Cutover and rollback commands with owner approval.

## Rules

- Process-running and port-open checks are necessary but not sufficient; include business/API/database assertions.
- A clone of a live database is not synchronized. Design native replication/final restore separately.
- Never weaken a failed test merely to achieve a pass.
- Use `references/app-matrix.md` and `references/known-issues.md` as prompts, not vendor certification.
