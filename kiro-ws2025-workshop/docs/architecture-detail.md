# Low-level infrastructure and application architecture

This document describes the exact AWS resources, software versions, ports, service configuration, and data flow deployed by this workshop.

## Infrastructure (CloudFormation `infra/lab.yaml`)

### Network

| Resource | Type | Detail |
|---|---|---|
| VPC | `10.42.0.0/16` | DNS hostnames and support enabled |
| Public Subnet A | `10.42.1.0/24` | First AZ, auto-assign public IP |
| Public Subnet B | `10.42.2.0/24` | Second AZ, auto-assign public IP (ALB requirement) |
| Internet Gateway | attached to VPC | Provides outbound for OS patching, upgrade runbook, and installer downloads |
| Route Table | `0.0.0.0/0 → IGW` | Associated with both subnets |

No NAT gateway, no private subnets, no VPC endpoints. This is a lab simplification; production should use private subnets with controlled egress.

### Security groups

| Security group | Inbound rules | Purpose |
|---|---|---|
| ALB SG | `0.0.0.0/0 → TCP 80` | Public HTTP access to the ALB |
| Workload SG | ALB SG → TCP 80, 8081, 8082 | Application ports from ALB only |

- No RDP (3389) rule exists. All management is through SSM Session Manager.
- Workload SG allows unrestricted outbound (`0.0.0.0/0`) for patching and downloads.
- Database ports (1433, 3306, 5432) are **not** opened in the security group; they are localhost-only.

### IAM

| Resource | Detail |
|---|---|
| Instance Role | `AmazonSSMManagedInstanceCore` managed policy + inline policy |
| Inline policy grants | `s3:GetObject` on payload ZIP + XAMPP installer; `s3:PutObject` on `logs/*`; `cloudformation:SignalResource` on the stack |
| Instance Profile | Attached to both APP01 and DATA01 |

The role has no `ec2:*`, `ssm:SendCommand`, or destructive permissions. Upgrade automation is driven from the **workstation** via the operator's own IAM identity.

### EC2 instances

| Instance | Type | Disk | AMI | Subnet | Signal timeout |
|---|---|---|---|---|---|
| APP01 | `t3.large` (2 vCPU, 8 GB) | 80 GB gp3 encrypted | Windows Server 2019 Full Base (latest SSM parameter) | Public A | 90 min |
| DATA01 | `t3.xlarge` (4 vCPU, 16 GB) | 100 GB gp3 encrypted | Same | Public A | 120 min |

Both instances use an IAM Role (via Instance Profile) for permissions — no access keys are stored on the instances. Metadata access is hardened with IMDSv2 as a security best practice.

### Load balancer

| Component | Detail |
|---|---|
| ALB | Internet-facing, HTTP only (port 80), spans Subnet A + B |
| Default action | Forward to APP01 IIS target group (port 80) |
| Rule priority 10 | Path `/spring*` or `/next*` → APP01 nginx target group (port 8081) |
| Rule priority 20 | Path `/data*` → DATA01 PHP target group (port 8082) |

Target groups:

| Target group | Port | Health check | Registered target |
|---|---|---|---|
| AppIisTargetGroup | 80 | `GET /health.html` → 200 | APP01 |
| AppNginxTargetGroup | 8081 | `GET /health` → 200 | APP01 |
| DataPhpTargetGroup | 8082 | `GET /data/api/status.php` → 200 | DATA01 |

---

## APP01 application stack

### Bootstrap sequence (`bootstrap/app01.ps1`)

```
IIS → Node.js 20 → Amazon Corretto 17 → Maven 3.9.9 → WinSW → nginx 1.26.2
→ Deploy Angular → Build Next.js → Build Spring Boot → Configure nginx
→ Install WinSW services → Open firewall → Validate health endpoints
```

### Installed software

| Component | Version | Install method | Location |
|---|---|---|---|
| IIS | Windows built-in | `Install-WindowsFeature` | Default |
| Node.js | 20.18.0 | MSI | `C:\Program Files\nodejs` |
| Amazon Corretto (JDK) | 17.0.12.7.1 | MSI | `C:\Program Files\Amazon Corretto\jdk17.*` |
| Apache Maven | 3.9.9 | ZIP extract | `C:\Tools\apache-maven-3.9.9` |
| nginx | 1.26.2 | ZIP extract | `C:\Tools\nginx-1.26.2` |
| WinSW | 2.12.0 | Single EXE | `C:\Installers\WinSW-x64.exe` |

### Applications

| Application | Framework | Build | Runtime | Port |
|---|---|---|---|---|
| Angular SPA | Angular (pre-built) | Static HTML shipped in repo | IIS serves `C:\inetpub\wwwroot` | 80 |
| Spring Boot API | Spring Boot 3 + Corretto 17 | Maven (`mvn -B package`) during bootstrap | `java -jar *.jar` via WinSW | 8080 |
| Next.js SSR | Next.js (standalone output) | `npm install` + `npm run build` during bootstrap | `node .next\standalone\server.js` via WinSW | 3000 |

### Services (WinSW-managed Windows services)

| Service name | Executable | Working directory | Environment variables | Start mode |
|---|---|---|---|---|
| `KiroSpring` | `java.exe -jar <app>.jar` | `apps\app01\spring` | — | Automatic |
| `KiroNext` | `node.exe .next\standalone\server.js` | `apps\app01\next` | `PORT=3000`, `HOSTNAME=0.0.0.0` | Automatic |
| `nginx` | `nginx.exe` | `C:\Tools\nginx-1.26.2` | — | Automatic |

All services restart on failure (10 sec delay). Logs go to `C:\Workshop\logs\<service>\`.

### nginx reverse proxy (`port 8081`)

```
location = /health     → 200 JSON {"status":"ok","marker":"NGINX_OK_V1"}
location /spring/      → proxy_pass http://127.0.0.1:8080/
location /next         → proxy_pass http://127.0.0.1:3000
```

### Windows firewall

| Rule | Port | Source |
|---|---|---|
| Kiro workshop nginx from VPC | TCP 8081 inbound | `10.42.0.0/16` |
| IIS (built-in) | TCP 80 inbound | Any (default Windows feature behavior) |

### Request flow

```
Internet → ALB :80
  │
  ├─ / or /health.html ──────────→ APP01 IIS :80 (Angular SPA, health page)
  │
  ├─ /spring/* ───→ ALB rule 10 → APP01 nginx :8081 /spring/ → Spring Boot :8080
  │
  └─ /next or /next/* ─→ ALB rule 10 → APP01 nginx :8081 /next → Next.js :3000
```

### Health check endpoints

| URL path | Expected response | Source |
|---|---|---|
| `/health.html` | `IIS_OK_V1` | IIS static file |
| `/spring/actuator/health` | `{"status":"UP"}` | Spring Boot Actuator |
| `/spring/api/info` | JSON with app info | Spring Boot controller |
| `/next` | SSR HTML page | Next.js |
| `/next/api/health` | `NEXT_API_OK_V1` | Next.js API route |
| `localhost:8081/health` | `NGINX_OK_V1` | nginx direct |

---

## DATA01 application stack

### Bootstrap sequence (`bootstrap/data01.ps1`)

```
Generate DB passwords → Install XAMPP 8.2.12 (Apache/PHP on port 8082)
→ Install MySQL 8.0.40 (ZIP) → Seed MySQL → Install PostgreSQL 15.8 → Seed PostgreSQL
→ Download SQL Server 2019 Express → Extract media → Install → Seed + verify
→ Open firewall → Validate PHP endpoint
```

### Installed software

| Component | Version | Install method | Location |
|---|---|---|---|
| XAMPP (Apache + PHP) | 8.2.12 | Silent installer from private S3 cache | `C:\xampp` |
| MySQL | 8.0.40 | ZIP extract + `mysqld --initialize-insecure` | `C:\Tools\mysql-8.0.40-winx64` |
| PostgreSQL | 15.8-1 | EnterpriseDB unattended installer | `C:\Program Files\PostgreSQL\15` |
| SQL Server Express | 2019 | Downloaded → extracted → `/Q` install | Default instance path `SQLEXPRESS` |

### Database details

| Engine | Instance/Service name | Port | Bind address | Auth | Database name |
|---|---|---|---|---|---|
| SQL Server 2019 Express | `MSSQL$SQLEXPRESS` | TCP disabled (shared memory/named pipe) | localhost | Windows integrated (`BUILTIN\Administrators`) | `KiroWorkshop` |
| MySQL 8.0.40 | `MySQL80` | 3306 | `127.0.0.1` | root + generated password | `kiro_workshop` |
| PostgreSQL 15.8 | `postgresql-x64-15` | 5432 | `127.0.0.1` | postgres + generated password | `kiro_workshop` |

- Passwords are random GUIDs generated at bootstrap time, stored only in `C:\Workshop\secrets\databases.json`.
- SQL Server has TCP disabled; connections use `localhost\SQLEXPRESS` via shared memory.
- All databases are seeded from SQL scripts under `apps/data01/sql/`.

### Data directories

| Engine | Data path |
|---|---|
| MySQL | `C:\ProgramData\KiroMySQL\data` |
| PostgreSQL | `C:\Program Files\PostgreSQL\15\data` |
| SQL Server | Default (`C:\Program Files\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQL\DATA`) |

### XAMPP / Apache / PHP

| Setting | Value |
|---|---|
| Listen port | 8082 (changed from default 80) |
| Document root | `C:\xampp\htdocs` |
| PHP application | `data/api/status.php` |
| Windows service | `Apache2.4` |

### Windows firewall

| Rule | Port | Source |
|---|---|---|
| Kiro workshop XAMPP from VPC | TCP 8082 inbound | `10.42.0.0/16` |

Database ports are not opened; all DB access is localhost via SSM Run Command scripts.

### Request flow

```
Internet → ALB :80
  │
  └─ /data/* ───→ ALB rule 20 → DATA01 Apache :8082 → PHP
```

### Health check endpoint

| URL path | Expected response | Source |
|---|---|---|
| `/data/api/status.php` | JSON with engine connectivity status | PHP checks all three DB engines |

---

## Backup architecture (pre-upgrade)

```
Workstation                          DATA01
    │                                   │
    ├─ python3 scripts/03_run_tests.py  │
    │   --phase backup-data             │
    │         │                         │
    │         └──── SSM Run Command ────┤
    │                                   ├─ BACKUP DATABASE ... TO DISK (SQL Server .bak)
    │                                   ├─ mysqldump --single-transaction (MySQL .sql)
    │                                   └─ pg_dump -Fc (PostgreSQL .dump)
    │                                   │
    │         ┌──── SSM output ─────────┘
    │         ▼                         
    └─ results/backups/summary.json     
```

Backups are stored on DATA01 at `C:\Workshop\backups\`. The upgrade script refuses to proceed with DATA01 until `summary.json` reports `"passed": true`.

---

## Upgrade and validation flow

```
Workstation                    AWS Systems Manager              EC2
    │                                │                           │
    ├─ 04_start_upgrade.py           │                           │
    │   (confirms server name)       │                           │
    │         │                      │                           │
    │         └─ StartAutomation ────┤                           │
    │              AWSEC2-Clone...   ├─ Create AMI from source ──┤
    │                                ├─ Launch temp instance ────┤
    │                                ├─ In-place Windows upgrade │
    │                                ├─ Sysprep + create AMI ────┤
    │                                └─ Terminate temp instance  │
    │         ┌─ Poll execution ─────┘                           │
    │         ▼                                                  │
    │   results/upgrades/<server>.json                            │
    │                                                            │
    ├─ 05_launch_validation.py                                   │
    │         └─ RunInstances (from upgraded AMI) ───────────────┤→ VAL-<server>
    │                                                            │
    ├─ 03_run_tests.py --phase post                              │
    │         └──── SSM Run Command on VAL instance ─────────────┤
    │         ┌──── test results ────────────────────────────────┘
    │         ▼
    └─ results/post/<server>-checks.json
```

---

## Cutover simulation (APP01 only)

```
Workstation                          ALB
    │                                 │
    ├─ 07_app_cutover.py --plan       │
    │         │                       │
    ├─ 07_app_cutover.py --execute    │
    │         ├─ RegisterTargets ─────┤─ VAL-APP01 added to both TGs
    │         ├─ Wait healthy ────────┤
    │         └─ DeregisterTargets ───┤─ Source APP01 removed
    │                                 │
    ├─ 07_app_cutover.py --rollback   │
    │         ├─ RegisterTargets ─────┤─ Source APP01 re-added
    │         ├─ Wait healthy ────────┤
    │         └─ DeregisterTargets ───┤─ VAL-APP01 removed
    │                                 │
    └─ results/cutover/               │
```

DATA01 is never cut over. Its validated clone proves compatibility only.

---

## Directory layout on instances

### APP01 (`C:\Workshop\`)

```
C:\Workshop\
├── payload\             # Extracted workshop ZIP
│   ├── bootstrap\       # app01.ps1, common.ps1
│   └── apps\app01\     # Angular, Next.js, Spring source
├── logs\                # WinSW service logs
│   ├── KiroSpring\
│   ├── KiroNext\
│   └── nginx\
├── bootstrap-status.json
└── bootstrap.log / transcript
```

### DATA01 (`C:\Workshop\`)

```
C:\Workshop\
├── payload\             # Extracted workshop ZIP
│   ├── bootstrap\       # data01.ps1, common.ps1
│   └── apps\data01\    # PHP app, SQL seed scripts
├── secrets\
│   └── databases.json   # Generated MySQL/PostgreSQL passwords
├── backups\             # Native DB backup files
│   ├── sqlserver-*.bak
│   ├── mysql-*.sql
│   └── postgresql-*.dump
├── bootstrap-status.json
└── bootstrap.log / transcript
```

---

## Port summary

| Instance | Port | Protocol | Listener | Accessible from |
|---|---|---|---|---|
| APP01 | 80 | HTTP | IIS | ALB only (SG rule) |
| APP01 | 8080 | HTTP | Spring Boot | localhost only (nginx proxies) |
| APP01 | 3000 | HTTP | Next.js | localhost only (nginx proxies) |
| APP01 | 8081 | HTTP | nginx | ALB via SG + VPC firewall rule |
| DATA01 | 8082 | HTTP | Apache/XAMPP | ALB via SG + VPC firewall rule |
| DATA01 | 3306 | TCP | MySQL | localhost only |
| DATA01 | 5432 | TCP | PostgreSQL | localhost only |
| DATA01 | — | Named pipe | SQL Server Express | localhost only (TCP disabled) |
