# AWS conventions

- Require `--region` and `--profile` in workshop commands.
- Tag resources with `Project=kiro-ws2025-workshop`, `Environment=lab`, and a role tag.
- Use IMDSv2, encrypted gp3 EBS, SSM instance profiles, and no direct internet ingress.
- Resolve Windows Server 2019 from `/aws/service/ami-windows-latest/Windows_Server-2019-English-Full-Base`.
- Windows Server 2025 clone upgrade requires Nitro, SSM Agent, TLS 1.2, PowerShell 3+, 20 GB free on boot, and outbound internet access.
- The AWS runbook does not support domain controllers, clusters, desktop Windows, RDSH, RDCB, RDVH, or RDWA.
- Runbook parameters used here: `IamInstanceProfile`, `InstanceId`, `SubnetId`, `TargetWindowsVersion=2025`, `KeepPreUpgradeImageBackUp=True`, `RebootInstanceBeforeTakingImage=False`.
- Do not add `AutomationAssumeRole` unless the installed runbook schema actually exposes it.
- Upgrade one workshop server at a time unless the user knowingly accepts additional concurrency and cost.
