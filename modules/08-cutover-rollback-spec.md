# Module 08 – APP01 cutover and rollback simulation

## Learning objective

Practice a health-gated ALB (Application Load Balancer) traffic switch from APP01's source instance to its validated Windows Server 2025 copy, then reverse it, and understand why this pattern only applies to APP01.

## Why only APP01

"Cutover" means switching real traffic from the old server to the new one. APP01 is a good candidate for this because it's stateless — the applications running on it (IIS, Spring Boot, Next.js, nginx) don't hold data that changes moment to moment, so a validated copy of APP01 is just as current as the source, and traffic can move between them safely.

DATA01 is different: it continues accepting writes (new database rows, updated files) after its image is created, so its clone becomes stale the moment new data arrives on the source. Never point production applications at VAL-DATA01 as an AMI-only cutover — that would mean silently losing every write that happened after the clone was taken. A real database cutover requires synchronization (ongoing replication) or a write freeze, a final backup/restore, validation, and RTO/RPO approval — none of which this workshop's AMI clone does on its own.

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

The plan shows source and validation instances, both target groups (the ALB routing config that decides which server receives traffic), health, proposed operations, and rollback — reviewing this before running the actual cutover lets you confirm the script will do what you expect.

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

The script registers VAL-APP01 (the validated Windows Server 2025 copy) with the load balancer's target groups, waits for healthy IIS and nginx target groups (so traffic only shifts once the new server is confirmed working), probes ALB routes to double-check real requests succeed, and only then deregisters source APP01 — this ordering means there's no gap where neither server is receiving traffic.

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

Measure and record recovery time. Target registration and application warm-up mean rollback is not literally instantaneous — even though the command itself runs quickly, the ALB needs time to detect the source instance as healthy again and start sending it real traffic, so "rollback" has a measurable duration, not zero.

## 4. Discuss production patterns with Kiro

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Ask it to compare:

1. Stateless ALB/Auto Scaling blue-green.
2. Singleton server with an approved maintenance window.
3. Stateful database with engine-native synchronization.

Require RTO/RPO, identity, sessions, file state, dependencies, observation periods, and rollback ownership in each design. This is an architecture discussion; do not call AWS or change the lab.

This shows that Kiro can help you explore architecture trade-offs — it compares multiple cutover patterns side by side, maps each to your constraints (RTO, RPO, state, dependencies), and helps you choose the right approach before committing to one.

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
