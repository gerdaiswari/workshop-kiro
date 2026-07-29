# Inventory assessment requirements

## Objective
Collect normalized, non-secret facts from APP01 and DATA01 through SSM before proposing an upgrade.

## Acceptance criteria

- Record instance ID, name, instance type, AMI, Nitro support signal, subnet, security groups, root size, SSM ping status, and tags.
- Record Windows caption/version/build, architecture, PowerShell/TLS state, free boot disk, installed features/programs, relevant services, listening ports, runtimes, and database engines.
- Detect excluded Windows roles and report them as blockers.
- Redact environment values, connection strings, passwords, certificates' private material, and user data.
- Write `results/inventory/inventory.json` with collection time and per-instance errors.
- Preserve `inventory/assumed-inventory.yaml`; measured facts supersede assumptions but do not silently rewrite them.
- Collection is read-only except for temporary command execution files managed by SSM.
