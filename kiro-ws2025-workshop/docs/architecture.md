# Workshop architecture

For the full low-level breakdown of every resource, port, service, version, and data flow, see [architecture-detail.md](architecture-detail.md).

## Logical flow

```mermaid
flowchart LR
  K[Kiro CLI workstation] -->|AWS CLI with approvals| SSM[AWS Systems Manager]
  K -->|read-only docs| MCP[AWS Knowledge MCP]
  SSM --> A[APP01 Windows 2019]
  SSM --> D[DATA01 Windows 2019]
  A --> UA[Upgraded APP01 AMI]
  D --> UD[Upgraded DATA01 AMI]
  UA --> VA[VAL-APP01 Windows 2025]
  UD --> VD[VAL-DATA01 Windows 2025]
  VA --> T[Post-upgrade tests]
  VD --> T
  T -->|APP01 pass + approval| ALB[ALB target switch simulation]
  T -->|DATA01 pass| COMP[Compatibility result only]
```

## AWS resources

```mermaid
flowchart TB
  Internet --> ALB[Public ALB :80]
  Internet --> IGW[Internet gateway]
  subgraph VPC[10.42.0.0/16]
    subgraph PublicSubnet[10.42.1.0/24; public IP egress]
      APP[APP01 t3.large]
      DATA[DATA01 t3.xlarge]
      VAL[Temporary upgrade and validation instances]
    end
    ALB -->|80, 8081| APP
    ALB -->|8082| DATA
    APP --> IGW
    DATA --> IGW
    VAL --> IGW
  end
  SSM[AWS Systems Manager] --> APP
  SSM --> DATA
  SSM --> VAL
```

The workload security group accepts application ports only from the ALB security group. It has no RDP rule and no direct internet ingress. Public addresses provide outbound connectivity because the AWS upgrade runbook must reach AWS services and Microsoft patch sources. Production environments should normally use private subnets, controlled NAT/proxy/VPC endpoints, and enterprise egress filtering.

## Application layout

- IIS port 80: compiled Angular SPA and `/health.html`.
- Spring Boot port 8080: Actuator and `/api/info`.
- Next.js port 3000: SSR page and `/api/health`.
- nginx port 8081: `/spring/*`, `/next/*`, and `/health` reverse-proxy routes.
- XAMPP Apache port 8082: PHP status endpoint.
- SQL Server Express local instance, MySQL 8 on 3306, PostgreSQL 15 on 5432.

Database ports are not permitted through the security group. Tests execute locally through SSM.

## Evidence lifecycle

```text
assumed inventory -> measured inventory -> compatibility report
                  -> baseline tests -> native DB backups
                  -> SSM execution -> upgraded AMI -> validation instance
                  -> post tests -> comparison -> decision
```

## Cutover boundary

APP01 is stateless in this lab. The cutover script registers the validated instance with both APP01 target groups, waits for health, and then deregisters the source. Rollback reverses that sequence.

DATA01 never enters this flow. Its clone proves only that the engines recover and queries work on Windows Server 2025. A real DATA01 migration requires replication or a write freeze plus final backup/restore, measured against RTO/RPO.
