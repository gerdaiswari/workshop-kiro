# Sample application and test matrix

This file describes the workshop build, not vendor certification for customer software.

## APP01

| Component | Windows service | Port | Mandatory evidence |
|---|---|---:|---|
| IIS + Angular | W3SVC | 80 | service running; `/health.html`; Angular marker at `/` |
| Spring Boot 3 | KiroSpring | 8080 | service running; Actuator `UP`; `/api/info` contract |
| Next.js 14 | KiroNext | 3000 | service running; page marker; `/api/health` JSON |
| nginx for Windows | nginx | 8081 | `nginx -t`; service running; `/spring/*` and `/next/*` proxy paths |

nginx on Windows is suitable for this compatibility demonstration, not a recommendation for high-scale production deployment.

## DATA01

| Component | Windows service | Local endpoint | Mandatory evidence |
|---|---|---|---|
| XAMPP Apache/PHP | Apache2.4 | 8082 | PHP status JSON and Apache service |
| SQL Server Express | `MSSQL$SQLEXPRESS` | local named instance | query, row count/checksum, native `.bak` |
| MySQL 8 | MySQL80 | 3306 localhost | ping/query, row count/checksum, `mysqldump` |
| PostgreSQL 15 | postgresql-x64-15 | 5432 localhost | readiness/query, row count/checksum, `pg_dump` |

XAMPP's bundled MariaDB is not started; the lab installs standalone MySQL to avoid a port/service conflict.

## Required customer additions for real applications

- Vendor-supported OS/runtime matrix.
- Authentication and authorization journeys.
- External dependencies, certificates, queues, file shares, scheduled jobs, and service accounts.
- Representative business transactions and reconciliation.
- Load/performance thresholds.
- RTO/RPO and rollback ownership.
