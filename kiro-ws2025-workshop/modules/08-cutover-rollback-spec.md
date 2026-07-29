# Module 08 – APP01 cutover and rollback simulation

## Why only APP01

APP01 contains synthetic stateless applications. DATA01 has continued accepting writes since its image was created; its clone is stale. Never point production applications at VAL-DATA01 as a “cutover.” A real database plan requires replication or a write freeze, final native backup/restore, validation, and RTO/RPO approval.

## Preview APP01 transition

```bash
python3 scripts/07_app_cutover.py --action plan \
  --region ap-southeast-1 --profile default --stack-name kiro-ws2025-lab
```

The plan shows source, validation instance, both target groups, current health, operations, and rollback.

## Cut over after explicit approval

```bash
python3 scripts/07_app_cutover.py --action cutover \
  --region ap-southeast-1 --profile default --stack-name kiro-ws2025-lab
```

It registers VAL-APP01, waits healthy in IIS and nginx target groups, probes ALB routes, and only then deregisters source APP01.

## Roll back

```bash
python3 scripts/07_app_cutover.py --action rollback \
  --region ap-southeast-1 --profile default --stack-name kiro-ws2025-lab
```

Measure and record recovery time. Target registration and application warm-up mean rollback is not literally instantaneous.

## Production discussion

Ask Kiro to design three different patterns for the real fleet:

1. Stateless ALB/Auto Scaling blue-green.
2. Singleton server with an approved maintenance window.
3. Stateful database with engine-native synchronization.

Require RTO/RPO, identity, sessions, file state, and dependency handling in each.

**Checkpoint:** APP01 transition and rollback have audit evidence; no DATA01 target changed.
