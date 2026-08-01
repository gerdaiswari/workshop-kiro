# Module 01 – Build the Windows Server 2019 lab

## Deploy

**Linux / macOS:**
```bash
./scripts/00_deploy.sh \
  --region us-east-1 \
  \
  --stack-name kiro-ws2025-lab
```

**Windows (PowerShell):**
```powershell
.\scripts\00_deploy.ps1 `
  -Region us-east-1 `
  -StackName kiro-ws2025-lab
```

The script:

1. **Create an S3 bucket** (AWS cloud storage) — if one doesn't exist yet in this region, create it to store files.
2. **Download XAMPP** (web application) — if not already saved locally, download it, check the security signature (SHA-256), upload to S3.
3. **Package bootstrap scripts and application source code** — prepare setup files that EC2 will automatically run when servers start.
4. **Deploy CloudFormation template** (`lab.yaml`) — this AWS template creates the network, security groups, and launches two EC2 servers (APP01 and DATA01).
5. **Wait for bootstrap signals** — both servers are running their setup scripts automatically; wait until they finish and confirm they're ready.
6. **Save outputs** — write server details (IP addresses, passwords, resource IDs) to `results/deployment/` folder.

Bootstrap can take 30–90 minutes because DATA01 is installing three databases at once (PostgreSQL, MySQL, SQL Server). SQL Server installation is especially slow because it arrives as one big compressed package — it must be unpacked and verified before installation can even start. This takes extra time. Just wait; do not cancel or restart.

## Inspect outputs

This one-line AWS CLI command works in PowerShell and Bash:

```text
aws cloudformation describe-stacks --stack-name kiro-ws2025-lab --query "Stacks[0].Outputs" --region us-east-1
```

Open `http://<LoadBalancerDns>/` and test each expected route:

| Route | Expected result |
|---|---|
| `/` | IIS-hosted Angular application |
| `/health.html` | IIS baseline health |
| `/spring/actuator/health` | nginx to Spring Boot |
| `/spring/api/info` | Spring Boot sample API |
| `/next` | nginx to Next.js |
| `/next/api/health` | Next.js API |
| `/data/api/status.php` | XAMPP/PHP status endpoint |

## Verify SSM

```text
aws ssm describe-instance-information --filters Key=tag:Project,Values=kiro-ws2025-workshop --region us-east-1
```

Both source instances must be `Online`. There is no RDP ingress; use Session Manager only if troubleshooting is required.

## Explore the applications with plain Kiro

Start with Kiro's default Vibe mode from the repository root—do not select a custom agent yet:

```text
kiro-cli chat --v3
```

Ask:

```text
Inspect apps/, bootstrap/, and infra/lab.yaml. Explain how each workload is built,
which Windows service owns it, which endpoint proves behavior, and which external
downloads make bootstrap non-hermetic. Do not make changes.
```

Notice what plain Kiro can already do: read the project, follow code relationships, and explain the architecture.

**Checkpoint:** stack complete, both instances SSM Online, all seven URL routes respond, and plain Kiro accurately identifies the APP01 and DATA01 components.

## If deployment rolls back

Extract failed resources and list durable bootstrap logs. These one-line commands work in PowerShell and Bash:

```text
aws cloudformation describe-stack-events --stack-name kiro-ws2025-lab --query "StackEvents[?contains(ResourceStatus, 'FAILED')].[Timestamp,LogicalResourceId,ResourceStatusReason]" --output table --region us-east-1

aws s3 ls s3://<artifact-bucket>/logs/kiro-ws2025-lab/ --recursive --region us-east-1
```

A stack in `ROLLBACK_COMPLETE` cannot be updated. After reviewing the resource IDs, delete only the failed stack metadata/resources and wait before retrying:

**Linux / macOS:**
```bash
aws cloudformation delete-stack --stack-name kiro-ws2025-lab \
  --region us-east-1
aws cloudformation wait stack-delete-complete --stack-name kiro-ws2025-lab \
  --region us-east-1
```

**Windows (PowerShell):**
```powershell
aws cloudformation delete-stack --stack-name kiro-ws2025-lab `
  --region us-east-1
aws cloudformation wait stack-delete-complete --stack-name kiro-ws2025-lab `
  --region us-east-1
```

The artifact bucket is intentionally outside the stack, so payloads and bootstrap diagnostics survive rollback.
