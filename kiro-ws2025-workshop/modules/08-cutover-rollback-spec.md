# Module 08 – APP01 cutover and rollback simulation

## Why only APP01

APP01 contains synthetic stateless applications. DATA01 continues accepting writes after its image is created, so its clone becomes stale. Never point production applications at VAL-DATA01 as an AMI-only cutover. A real database cutover requires synchronization or a write freeze, final backup/restore, validation, and RTO/RPO approval.

## 1. Preview the APP01 transition

**Windows PowerShell:**

```powershell
py -3 scripts\07_app_cutover.py --action plan `
  --region us-east-1 --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/07_app_cutover.py --action plan \
  --region us-east-1 --stack-name kiro-ws2025-lab
```

The plan shows source and validation instances, both target groups, health, proposed operations, and rollback.

## 2. Cut over after explicit approval

**Windows PowerShell:**

```powershell
py -3 scripts\07_app_cutover.py --action cutover `
  --region us-east-1 --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/07_app_cutover.py --action cutover \
  --region us-east-1 --stack-name kiro-ws2025-lab
```

The script registers VAL-APP01, waits for healthy IIS and nginx target groups, probes ALB routes, and only then deregisters source APP01.

## 3. Roll back

**Windows PowerShell:**

```powershell
py -3 scripts\07_app_cutover.py --action rollback `
  --region us-east-1 --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/07_app_cutover.py --action rollback \
  --region us-east-1 --stack-name kiro-ws2025-lab
```

Measure and record recovery time. Target registration and application warm-up mean rollback is not literally instantaneous.

## 4. Discuss production patterns with Kiro

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Ask it to compare:

1. Stateless ALB/Auto Scaling blue-green.
2. Singleton server with an approved maintenance window.
3. Stateful database with engine-native synchronization.

Require RTO/RPO, identity, sessions, file state, dependencies, observation periods, and rollback ownership in each design. This is an architecture discussion; do not call AWS or change the lab.

## Transfer to your environment

- **Lab exercise:** APP01 demonstrates health-gated ALB target switching and reversal; DATA01 intentionally demonstrates why a live stateful clone is not cutover-ready.
- **Reusable pattern:** choose cutover architecture from workload state, identity, sessions, dependencies, RTO/RPO, observation time, and rollback ownership. Register/validate before removing the old path when the architecture supports it.
- **Adapt before reuse:** design separately for stateless fleets, singleton servers, databases, domain/identity-sensitive workloads, file state, queues, scheduled jobs, and external consumers. For stateful systems, add replication or write freeze plus final backup/restore and reconciliation. Measure rollback; never describe it as instant.

Adaptation prompt:

```text
Classify my workload and produce a cutover/rollback design with prerequisites,
health gates, data synchronization, observation period, RTO/RPO, owners, stop
conditions, and commands to be reviewed. Do not execute or assume it is stateless.
```

**Checkpoint:** APP01 transition and rollback have audit evidence, and no DATA01 target was changed.
