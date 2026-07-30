# External dependency manifest

The workshop pins application and most runtime versions, but still downloads binaries at bootstrap time. Mirror and checksum these artifacts before enterprise use.

| Component | Version | Source |
|---|---:|---|
| Node.js | 20.18.0 | nodejs.org MSI |
| Angular | 17.3.12 | Pre-built static HTML shipped in payload (no npm install on instance) |
| Next.js | 14.2.15 | npm registry |
| React | 18.3.1 | npm registry |
| Amazon Corretto | 17.0.12.7.1 | corretto.aws MSI |
| Maven | 3.9.9 | archive.apache.org ZIP |
| Spring Boot | 3.3.5 | Maven Central |
| nginx for Windows | 1.26.2 | nginx.org ZIP |
| WinSW | 2.12.0 | GitHub release |
| XAMPP | 8.2.12 | SourceForge fetched by deploy script, pinned SHA-256, private S3 delivery |
| MySQL | 8.0.40 | cdn.mysql.com archive ZIP |
| PostgreSQL | 15.8-1 | EnterpriseDB installer |
| SQL Server Express | 2019 | Microsoft web bootstrapper downloads `SQLEXPR_x64_ENU.exe`; package is extracted before unattended `setup.exe` |

## Non-hermetic elements

- npm/Maven transitive dependencies are downloaded during instance bootstrap.
- SQL Server Express uses Microsoft's current download endpoint for its 2019 bootstrapper.
- SourceForge can throttle or return HTML to EC2 clients. The deployment script therefore downloads XAMPP from the operator workstation, validates the pinned SHA-256 `12e818ce5aec79fe646606df3a80b35da865ec0213646ad7c92044dcfcec7535`, and caches it under `dependencies/` in the private artifact bucket. DATA01 never downloads XAMPP from SourceForge.
- EnterpriseDB may change redirects or retire old artifacts.
- Public repositories can throttle downloads.

For a reliable classroom event, place reviewed binaries and lock files in a private, versioned S3 artifact bucket, validate SHA-256 hashes, and pre-bake the source AMIs.
