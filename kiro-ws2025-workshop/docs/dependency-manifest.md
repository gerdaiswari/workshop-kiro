# External dependency manifest

The workshop pins application and most runtime versions, but still downloads binaries at bootstrap time. Mirror and checksum these artifacts before enterprise use.

| Component | Version | Source |
|---|---:|---|
| Node.js | 20.18.0 | nodejs.org MSI |
| Angular | 17.3.12 | npm registry |
| Next.js | 14.2.15 | npm registry |
| React | 18.3.1 | npm registry |
| Amazon Corretto | 17.0.12.7.1 | corretto.aws MSI |
| Maven | 3.9.9 | archive.apache.org ZIP |
| Spring Boot | 3.3.5 | Maven Central |
| nginx for Windows | 1.26.2 | nginx.org ZIP |
| WinSW | 2.12.0 | GitHub release |
| XAMPP | 8.2.12 | SourceForge installer |
| MySQL | 8.0.40 | dev.mysql.com ZIP |
| PostgreSQL | 15.8-1 | EnterpriseDB installer |
| SQL Server Express | 2019 | Microsoft web bootstrapper |

## Non-hermetic elements

- npm/Maven transitive dependencies are downloaded during instance bootstrap.
- SQL Server Express uses Microsoft's current download endpoint for its 2019 bootstrapper.
- SourceForge and EnterpriseDB may change redirects or retire old artifacts.
- Public repositories can throttle downloads.

For a reliable classroom event, place reviewed binaries and lock files in a private, versioned S3 artifact bucket, validate SHA-256 hashes, and pre-bake the source AMIs.
