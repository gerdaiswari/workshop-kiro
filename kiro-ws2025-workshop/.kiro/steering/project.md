# Project context

- Workshop name: Kiro Windows Server 2019 to 2025 Upgrade Lab.
- Source environment: two AWS EC2 Windows Server 2019 English Full Base instances.
- APP01 workloads: IIS-hosted Angular, Spring Boot on 8080, Next.js on 3000, nginx on 8081.
- DATA01 workloads: XAMPP Apache/PHP on 8082, SQL Server Express, MySQL 8, PostgreSQL 15.
- Management: AWS Systems Manager only; no inbound RDP.
- Upgrade engine: AWS-owned `AWSEC2-CloneInstanceAndUpgradeWindows`.
- Target: Windows Server 2025 upgraded AMIs and isolated validation instances.
- Evidence lives in `results/`; generated evidence is not a secret store.
- The assumed inventory is `inventory/assumed-inventory.yaml`; measured inventory supersedes assumptions.

## Definition of done

A server is upgrade-compatible only when its upgraded validation instance reports Windows Server 2025, SSM is online, mandatory service/API/database tests pass, and baseline/post evidence contains no unexplained regression. APP01 cutover additionally requires healthy ALB targets. DATA01 has no cutover in this workshop.
