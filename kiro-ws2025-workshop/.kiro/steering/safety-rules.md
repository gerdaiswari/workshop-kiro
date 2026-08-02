---
inclusion: always
---

# Upgrade safety rules

1. Never execute an AWS mutation unless the user explicitly approves that exact phase in the current conversation.
2. Never terminate a source instance, delete recovery artifacts, change traffic or DNS, or clean up resources as an implicit follow-up.
3. Prefer describe/get/list operations. Before a mutation, show the proposed action, affected resource IDs, rollback, expected duration, and cost impact.
4. Run `python3 tests/static/validate_repo.py` after repository changes.
5. Capture measured inventory and baseline evidence before upgrade, then post-upgrade evidence before promotion.
6. Do not claim zero downtime, instant rollback, or application compatibility without architecture and measured evidence.
7. Treat every AMI clone as a point-in-time copy, not data replication. Do not promote a stateful clone while its source continues accepting unsynchronized writes.
8. A mandatory test failure blocks promotion. Diagnose and remediate the validation copy; do not suppress or weaken the test without owner approval.
9. Never store passwords, private keys, AWS credentials, or database dumps in Git.
10. Require separate approval for cutover, rollback, recovery-artifact deletion, and cleanup.
