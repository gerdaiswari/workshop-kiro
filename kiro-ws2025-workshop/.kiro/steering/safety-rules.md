# Safety rules

1. Never execute an AWS mutation unless the user explicitly approves that exact phase in the current conversation.
2. Never terminate source instances, delete snapshots/AMIs, delete the stack, change DNS, or switch ALB targets as an implicit follow-up.
3. Prefer describe/get/list operations. Show the proposed command, affected resource IDs, rollback, and expected cost before mutation.
4. Run `python3 tests/static/validate_repo.py` after repository changes.
5. Capture baseline evidence before upgrade and post-upgrade evidence before promotion.
6. Do not claim “zero downtime,” “instant rollback,” or “application compatible” without architecture and measured evidence.
7. An AMI clone is point-in-time. It is not database replication. Never propose DATA01 clone cutover while the source accepts writes.
8. Test failure blocks promotion. Diagnose and remediate the validation copy; do not suppress or weaken the test without owner approval.
9. Never store passwords, private keys, AWS credentials, or database dumps in Git. Lab database passwords are generated locally on DATA01.
10. Cleanup is a separate, explicitly approved task.
