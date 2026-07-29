# Cutover and rollback requirements

## Objective
Demonstrate an application-tier ALB switch and measured rollback while explicitly excluding stateful database cutover.

## Acceptance criteria

- Only a tagged VAL-APP01 instance may be promoted.
- Post-upgrade APP01 tests and target health must pass before source deregistration.
- Show source/target IDs, target groups, commands, health wait, rollback, and expected user impact before approval.
- Cutover registers VAL-APP01 in IIS and nginx target groups, waits healthy, then deregisters source APP01.
- Rollback registers source APP01, waits healthy, then deregisters VAL-APP01.
- Capture ALB health and endpoint tests after either action.
- DATA01 is never switched. Document the separate replication/write-freeze/final-restore design a production database would require.
