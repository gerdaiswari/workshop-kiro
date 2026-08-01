# Kiro Workshop: Windows Server 2019 to 2025 on AWS

Build two representative Windows Server 2019 EC2 servers, use Kiro CLI to inventory and assess them, create automated tests that can be run again after every change, clone-upgrade them with the AWS-owned Systems Manager runbook, and validate Windows Server 2025 copies before a cutover simulation.

> **Purpose:** Demonstrate how Kiro assists you for the Windows Server upgrade process. AWS Systems Manager performs the OS upgrade; deterministic scripts and tests decide pass/fail; you approve every AWS change before it runs.

## What the lab builds

| Server | Workloads | Purpose |
|---|---|---|
| APP01 | IIS + Angular, Spring Boot/Java, Next.js/Node.js, nginx | Stateless application compatibility and ALB cutover/rollback |
| DATA01 | XAMPP/Apache/PHP, SQL Server Express, MySQL, PostgreSQL | Database service recovery, integrity, backup, and query compatibility |

Both start from the AWS Windows Server 2019 English Full Base AMI on Nitro-based EC2. Administration is SSM-only. No RDP key pair is required. Instances have outbound internet through public IPs for package installation and Microsoft patch access, but their security group has **no direct internet ingress**. A public ALB exposes only the demo HTTP routes.

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
4. DATA01's upgraded AMI captures the server state at clone time. It's a compatibility check, not a production cutover solution. Real cutover requires syncing data (replication) or stopping writes, taking a final backup, and restoring to the new server.
5. APP01 is the only server with a simulated ALB cutover. You must wait for health checks to pass and the application to fully recover. Note: rollback takes time; it's not instant.
6. The lab doesn't include domain controllers, failover clusters, Remote Desktop roles (RDSH, RDCB, RDVH, RDWA), or BYOL media.

## Architecture overview

Before starting, review the lab infrastructure and application design:

- [Architecture overview](docs/architecture.md) — logical flow, AWS resources, application layout, and cutover boundary
- [Detailed architecture](docs/architecture-detail.md) — exact versions, ports, services, data flow, and directory layout on each instance

## Prerequisites

- Windows, macOS, or Linux workstation with Kiro CLI 2.15.2+ (`kiro-cli chat --v3` selects the v3 engine), AWS CLI v2, and Python 3.9+. Git is optional (only needed if cloning the repo).
- AWS permissions for CloudFormation, EC2, IAM, S3, ELBv2, and Systems Manager Automation.
- A region with the Windows Server 2019 public AMI SSM parameter and the AWS runbook (workshop defaults to us-east-1).

## Workshop path

This is a facilitator-led, hands-on workshop. Modules 00–01 and the plain-Kiro introduction are completed first. During the long-running upgrade, participants continue with read-only/low-risk Kiro feature modules, then return to validation and cutover once both upgrades finish.

| Order | Module | Topic | Duration |
|---:|---|---|---:|
| Pre-work | [00](modules/00-prerequisites.md) | Prerequisites, credentials, regional checks, and cost | 15 min |
| Pre-work | [01](modules/01-lab-setup.md) | Deploy and verify the Windows Server 2019 lab | 30 min + bootstrap wait |
| 1 | [02](modules/02-steering-and-permissions.md) | Create steering, an agent, and tool permissions | 20 min |
| 2 | [03](modules/03-inventory-spec.md) | Inventory through SSM and Kiro Spec | 15 min |
| 3 | [04](modules/04-compatibility-spec.md) | Compatibility analysis and evidence challenge | 10 min |
| 4 | [05](modules/05-hooks-and-safety.md) | Create hooks, capture baselines and native backups | 10 min |
| 5 | [06](modules/06-clone-upgrade-spec.md) | Start APP01 and DATA01 clone-upgrades in separate terminals | 5 min to start, then wait for both runbooks to finish |
| 6 | [09](modules/09-mcp-integration.md) | Add and use AWS Knowledge MCP while upgrades run | 20 min |
| 7 | [10](modules/10-skills-and-reuse.md) | Create a reusable skill and fleet plan while upgrades run | 20 min |
| 8 | [10B](modules/10b-agents-and-subagents.md) | Create specialized agents, models, and subagents while upgrades run | 25 min |
| 9 | [07](modules/07-validation-spec.md) | Launch Windows Server 2025 copies and run post-upgrade tests | 20 min |
| 10 | [08](modules/08-cutover-rollback-spec.md) | Cutover/rollback simulation; DATA01 compatibility boundary | 15 min |
| 11 | [11](modules/11-cleanup.md) | Remove all billable resources | 10 min |

Upgrade duration is controlled by AWS Systems Manager and Windows Update and can vary. Modules 09, 10, and 10B are designed to fill that wait; do not skip success checks in Module 07 merely to keep to a schedule.

## Cost estimation

Pricing varies by region. The largest charges are Windows EC2 runtime, temporary upgrade instances, EBS snapshots, and the ALB. DATA01 defaults to `t3.xlarge` because it runs three database engines. Budget **USD 15–35** if both upgrades run for several hours; this is an estimate, not a quote.

## Cleanup

Run `scripts/08_cleanup.sh` on Linux/macOS or `scripts\08_cleanup.ps1` on Windows **even if something fails**. This deletes all lab resources and stops charges.

## Authoritative references

- `kiro-cli --help-all` – installed CLI commands and global options
- `kiro-cli chat --help` – v3, Spec mode, agents, models, effort, and trust options
- `kiro-cli agent --help` – custom-agent management
- Inside chat, `/guide <question>` – embedded Kiro CLI documentation
- [AWS Knowledge MCP Server](https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server)
- [AWSEC2-CloneInstanceAndUpgradeWindows](https://docs.aws.amazon.com/systems-manager-automation-runbooks/latest/userguide/automation-awsec2-CloneInstanceAndUpgradeWindows.html)
