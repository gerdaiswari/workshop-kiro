# Known risks and checks

These are assessment prompts. Verify current AWS and vendor documentation for every real workload.

## AWS runbook blockers

- Source is not a supported Windows Server version/edition.
- Windows Server 2025 source instance is not Nitro-based.
- SSM Agent is missing/offline, TLS 1.2 unavailable, PowerShell below 3.0, boot free space below 20 GB, or no required outbound internet.
- Domain controller, cluster, Windows desktop, RDSH, RDCB, RDVH, or RDWA role detected.
- BYOL media/licensing requirements are unresolved.

## Application risks

- Runtime or native module is not vendor-supported on Windows Server 2025.
- Service account, ACL, certificate private key, ODBC/JDBC driver, COM registration, scheduled task, or hard-coded path is missing.
- IIS modules, URL Rewrite, Windows authentication, or app-pool settings are undocumented.
- nginx/Apache/PHP configuration parses but a business route still fails.
- Node native modules or Java cryptography/TLS behavior changes after OS/runtime updates.
- Monitoring reports process health but no business transaction exists.

## Database risks

- AMI/EBS copy of an active engine is crash-consistent at best unless application-consistent measures are used.
- A tested clone becomes stale while source writes continue.
- Engine version may run but lack vendor certification on the target OS.
- Service identity, file ACL, locale/collation, extensions/plugins, backup path, and client drivers may change behavior.
- A compatibility query is not a production cutover plan; require replication or final write-freeze/backup/restore.

## Decision language

- **Pass:** objective evidence meets the defined criterion.
- **Warning:** compatible in the lab but operational or vendor risk remains.
- **Unknown:** required fact or owner decision is missing.
- **Blocker:** AWS path unsupported or mandatory safety/test criterion failed.
