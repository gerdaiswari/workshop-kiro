# Kiro Workshop: Windows Server 2019 to 2025 on AWS

Build two representative Windows Server 2019 EC2 servers, use Kiro CLI to inventory and assess them, create repeatable tests, clone-upgrade them with the AWS-owned Systems Manager runbook, and validate Windows Server 2025 copies before an APP01-only cutover simulation.

> **Purpose:** Demonstrate how Kiro assists engineers. AWS Systems Manager performs the OS upgrade; deterministic scripts and tests decide pass/fail; a human authorizes AWS mutations.

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

## Prerequisites

- Windows, macOS, or Linux workstation with Kiro CLI 2.15.2+ (`kiro-cli chat --v3` selects the v3 engine), AWS CLI v2, Python 3.11+, and Git.
- AWS permissions for CloudFormation, EC2, IAM, S3, ELBv2, and Systems Manager Automation.
- A region with the Windows Server 2019 public AMI SSM parameter and the AWS runbook (workshop defaults to us-east-1).
- Quota for three to six Nitro Windows instances during the exercise.

No RDP key pair is required.

## Workshop path

| Module | Topic | Active time |
|---|---|---:|
| [00](modules/00-prerequisites.md) | Prerequisites, cost, assumptions | 15 min |
| [01](modules/01-lab-setup.md) | Deploy and verify WS2019 lab | 30 min + bootstrap |
| [02](modules/02-steering-and-permissions.md) | Configure Kiro, steering, agent, and tool trust | 20 min |
| [03](modules/03-inventory-spec.md) | Inventory through SSM and Kiro Spec | 25 min |
| [04](modules/04-compatibility-spec.md) | Compatibility analysis and remediation plan | 25 min |
| [05](modules/05-hooks-and-safety.md) | Hooks, approvals, baseline evidence | 20 min |
| [06](modules/06-clone-upgrade-spec.md) | Start and monitor clone upgrades | 30 min active + up to 4 hr wait |
| [07](modules/07-validation-spec.md) | Launch WS2025 copies, test, inject and fix failure | 35 min |
| [08](modules/08-cutover-rollback-spec.md) | APP01 cutover/rollback simulation; DATA01 caveat | 20 min |
| [09](modules/09-mcp-integration.md) | AWS Knowledge MCP exercises | 15 min |
| [10](modules/10-skills-and-reuse.md) | Reuse for a 40-server fleet | 15 min |
| [10B](modules/10b-agents-and-subagents.md) | Custom agents, subagents, multi-model strategies | 25 min |
| [11](modules/11-cleanup.md) | Remove all billable resources | 10 min |

## Quick start

**Linux / macOS:**
```bash
cd kiro-ws2025-workshop
python3 scripts/check_kiro_prereqs.py
aws sts get-caller-identity --profile default --region us-east-1
python3 tests/static/validate_repo.py
./scripts/00_deploy.sh --region us-east-1 --profile default
kiro-cli chat --v3 --agent windows-upgrade
```

**Windows (PowerShell):**
```powershell
cd kiro-ws2025-workshop
py -3 scripts\check_kiro_prereqs.py
aws sts get-caller-identity --profile default --region us-east-1
py -3 tests\static\validate_repo.py
.\scripts\00_deploy.ps1 -Region us-east-1 -Profile default
kiro-cli chat --v3 --agent windows-upgrade-windows
```

Then follow Module 02 onward. The deployment script prints stack outputs and writes non-secret state under `results/`.

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
