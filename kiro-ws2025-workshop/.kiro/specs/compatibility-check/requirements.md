# Compatibility check requirements

## Objective
Turn measured inventory into a traceable Windows Server 2025 readiness decision.

## Acceptance criteria

- Evaluate AWS runbook prerequisites: supported source, Nitro, SSM online, TLS 1.2, PowerShell 3+, boot free space >=20 GiB, internet egress, and unsupported Windows roles.
- Evaluate every expected application/database component; missing version facts are `unknown`, never `pass`.
- Distinguish AWS technical eligibility, vendor support, application test coverage, and production cutover readiness.
- Treat DATA01 as stateful and explicitly reject AMI-only live cutover.
- Produce `results/compatibility/report.json` and `.md` with `pass`, `warning`, `blocker`, or `unknown` checks.
- Overall status is `blocked` if any blocker exists and `conditional` if unknowns remain.
