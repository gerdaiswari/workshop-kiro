# Inventory assessment design

`01_collect_inventory.py` reads CloudFormation outputs, calls EC2/SSM describe APIs, and sends `scripts/remote/collect_inventory.ps1` to both instances with `AWS-RunPowerShellScript`. The remote script emits one compressed JSON object. The local runner combines AWS and OS facts into a versioned document.

Failure is per-server: one unavailable instance does not discard the other result, but the overall inventory status becomes `incomplete`. The script never reads application configuration files or secret values. Static validation checks required output fields and prevents accidental secret-key names.

Output schema:

```text
schema_version, collected_at, stack, servers[]
server: logical_name, instance_id, aws, os, disks, features,
        programs, services, listeners, runtimes, blockers, errors
```
