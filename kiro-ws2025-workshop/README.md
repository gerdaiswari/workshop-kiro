# Kiro Workshop: Windows Server 2019 to 2025 on AWS

Build two representative Windows Server 2019 EC2 servers, use Kiro CLI to inventory and assess them, create repeatable tests, clone-upgrade them with the AWS-owned Systems Manager runbook, and validate Windows Server 2025 copies before an APP01-only cutover simulation.

> **Purpose:** Demonstrate how Kiro assists engineers. AWS Systems Manager performs the OS upgrade; deterministic scripts and tests decide pass/fail; you approve every AWS change before it runs.

## What the lab builds

| Server | Workloads | Purpose |
|---|---|---|
| APP01 | IIS + Angular, Spring Boot/Java, Next.js/Node.js, nginx | Stateless application compatibility and ALB cutover/rollback |
| DATA01 | XAMPP/Apache/PHP, SQL Server Express, MySQL, PostgreSQL | Database service recovery, integrity, backup, and query compatibility |

Both start from the AWS Windows Server 2019 English Full Base AMI on Nitro-based EC2. Administration is SSM-only. Instances have outbound internet through public IPs for package installation and Microsoft patch access, but their security group has **no direct internet ingress**. A public ALB exposes only the demo HTTP routes.

## What Kiro demonstrates

- **Specs:** requirements, design, tasks, and verification evidence.
- **Steering:** persistent safety, AWS, and testing rules.
- **Custom agent:** focused tools and conservative trust.
- **Multi-model agents:** strong models for planning/review, fast models for execution.
- **Subagent pipelines:** orchestrate plan → execute → review workflows across specialized agents.
- **Hooks:** block selected destructive shell commands and run static checks after Kiro writes files.
- **Skills:** reusable Windows upgrade operating procedure and compatibility references.
- **MCP:** read-only AWS Knowledge MCP for current AWS documentation.
- **Code intelligence and subagents:** inspect scripts/apps and obtain independent reviews.
- **Tool trust:** agent `allowedTools`, tool restrictions, approval prompts, and supported hooks.

## Safety boundaries

1. `AWSEC2-CloneInstanceAndUpgradeWindows` creates an AMI, upgrades a temporary instance, outputs an upgraded AMI, and terminates the temporary instance. It does not make the source instance Windows Server 2025.
2. The runbook can take about two hours **per server** and creates billable resources.
3. Source instances are not rebooted by this workshop (`RebootInstanceBeforeTakingImage=False`), but AMI creation still performs storage snapshots. Native database backups are taken first.
4. DATA01's upgraded AMI is a point-in-time **compatibility copy**, not a production database cutover solution. Real database cutover requires replication or a controlled write outage and final restore.
5. Only APP01 has an optional ALB target switch exercise. Rollback is not called “instant”; it includes target health and application recovery time.
6. No domain controllers, failover clusters, RDSH/RDCB/RDVH/RDWA roles, or BYOL media are used.

## Architecture overview

Before starting, review the lab infrastructure and application design:

- [Architecture overview](docs/architecture.md) — logical flow, AWS resources, application layout, and cutover boundary
- [Detailed architecture](docs/architecture-detail.md) — exact versions, ports, services, data flow, and directory layout on each instance

## Prerequisites

- Windows, macOS, or Linux workstation with Kiro CLI 2.15.2+ (`kiro-cli chat --v3` selects the v3 engine), AWS CLI v2, and Python 3.9+. Git is optional (only needed if cloning the repo).
- AWS permissions for CloudFormation, EC2, IAM, S3, ELBv2, and Systems Manager Automation.
- A region with the Windows Server 2019 public AMI SSM parameter and the AWS runbook (workshop defaults to us-east-1).
- Quota for three to six Nitro Windows instances during the exercise.

No RDP key pair is required.

## Workshop path

Modules 00–01 and the plain-Kiro introduction are completed before the facilitated hands-on begins. During the long-running upgrade, participants continue with read-only/low-risk Kiro feature modules, then return to validation and cutover.

| Order | Module | Topic | Timing |
|---:|---|---|---:|
| Pre-work | [00](modules/00-prerequisites.md) | Prerequisites, credentials, regional checks, and cost | Before 14:30 |
| Pre-work | [01](modules/01-lab-setup.md) | Deploy and verify the Windows Server 2019 lab | Before 14:30 |
| 1 | [02](modules/02-steering-and-permissions.md) | Create steering, an agent, and tool permissions | 20 min |
| 2 | [03](modules/03-inventory-spec.md) | Inventory through SSM and Kiro Spec | 15 min |
| 3 | [04](modules/04-compatibility-spec.md) | Compatibility analysis and evidence challenge | 10 min |
| 4 | [05](modules/05-hooks-and-safety.md) | Create hooks, capture baselines and native backups | 10 min facilitated |
| 5 | [06](modules/06-clone-upgrade-spec.md) | Start APP01 and DATA01 clone-upgrades in separate terminals | 5 min start + background wait |
| 6 | [09](modules/09-mcp-integration.md) | Add and use AWS Knowledge MCP while upgrades run | 20 min |
| 7 | [10](modules/10-skills-and-reuse.md) | Create a reusable skill and fleet plan while upgrades run | 20 min |
| 8 | [10B](modules/10b-agents-and-subagents.md) | Create specialized agents, models, and subagents while upgrades run | 25 min |
| 9 | [07](modules/07-validation-spec.md) | Launch Windows Server 2025 copies and run post-upgrade tests | 20 min |
| 10 | [08](modules/08-cutover-rollback-spec.md) | APP01 cutover/rollback simulation; DATA01 compatibility boundary | 15 min |
| 11 | [11](modules/11-cleanup.md) | Remove all billable resources | 10 min |

### Facilitated schedule

| Time | Activity |
|---|---|
| 14:30–14:50 | Module 02 — create steering, agent, and permissions |
| 14:50–15:05 | Module 03 — inventory with Spec mode |
| 15:05–15:15 | Module 04 — compatibility assessment |
| 15:15–15:25 | Module 05 — hooks, baseline tests, and database backups |
| 15:25–15:30 | Module 06 — start APP01 and DATA01 upgrades in separate terminals |
| **15:30–16:00** | **Break — both upgrades continue running** |
| 16:00–16:20 | Module 09 — add AWS Knowledge MCP |
| 16:20–16:40 | Module 10 — create and exercise a skill |
| 16:40–17:05 | Module 10B — models, specialized agents, and subagents |
| 17:05–17:25 | Inspect upgrade progress; complete advanced exercise/Q&A if still running |
| 17:25–17:45 | Module 07 — validation and comparison (after both upgrades succeed) |
| 17:45–18:00 | Module 08 — APP01 cutover and rollback simulation |
| 18:00–18:10 | Module 11 — cleanup and wrap-up |

Upgrade duration is controlled by AWS Systems Manager and Windows Update and can vary. Do not skip success checks merely to keep the agenda. The facilitator should allow schedule buffer or prepare a documented fallback environment if either runbook is still running at 17:25.

## Quick start

**Linux / macOS:**
```bash
cd kiro-ws2025-workshop
python3 scripts/check_kiro_prereqs.py
aws sts get-caller-identity
python3 tests/static/validate_repo.py
./scripts/00_deploy.sh --region us-east-1
kiro-cli chat --v3
```

**Windows (PowerShell):**
```powershell
cd kiro-ws2025-workshop
py -3 scripts\check_kiro_prereqs.py
aws sts get-caller-identity
py -3 tests\static\validate_repo.py
.\scripts\00_deploy.ps1 -Region us-east-1
kiro-cli chat --v3
```

Then follow Module 01 to explore the project with plain Kiro. In Module 02, participants create steering and their own custom agent before using agent-based exercises.

## Expected URL routes

- `/` – IIS-hosted Angular application
- `/health.html` – IIS baseline health
- `/spring/actuator/health` – nginx to Spring Boot
- `/spring/api/info` – Spring Boot sample API
- `/next` – nginx to Next.js
- `/next/api/health` – Next.js API
- `/data/api/status.php` – XAMPP/PHP status endpoint

## Costs and cleanup

Pricing varies by region. The largest charges are Windows EC2 runtime, temporary upgrade instances, EBS snapshots, and the ALB. DATA01 defaults to `t3.xlarge` because it runs three database engines. Budget **USD 15–35** if both upgrades run for several hours; this is an estimate, not a quote. Run `scripts/08_cleanup.sh` on Linux/macOS or `scripts\08_cleanup.ps1` on Windows even if a module fails.

## Authoritative references

- `kiro-cli --help-all` – installed CLI commands and global options
- `kiro-cli chat --help` – v3, Spec mode, agents, models, effort, and trust options
- `kiro-cli agent --help` – custom-agent management
- Inside chat, `/guide <question>` – embedded Kiro CLI documentation
- [AWS Knowledge MCP Server](https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server)
- [AWSEC2-CloneInstanceAndUpgradeWindows](https://docs.aws.amazon.com/systems-manager-automation-runbooks/latest/userguide/automation-awsec2-CloneInstanceAndUpgradeWindows.html)
