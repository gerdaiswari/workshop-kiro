# Module 00 – Prerequisites and assumptions

## Learning objective
Prepare a Windows, Linux, or macOS workstation; verify Kiro CLI and AWS access; and understand the workshop's safety and cost boundaries.

## 1. Choose your workstation instructions

Use the column that matches the computer where you run Kiro CLI and AWS CLI. The EC2 workloads themselves are Windows regardless of your workstation choice.

| Workstation | Terminal | Deployment script | Python command in examples |
|---|---|---|---|
| Windows | PowerShell 5.1+ or PowerShell 7+ | `scripts\00_deploy.ps1` | `py -3` |
| Linux or macOS | Bash | `scripts/00_deploy.sh` | `python3` |

Windows does **not** require WSL or Git Bash for this workshop.

## 2. Install the required tools

Install these tools using their official installation instructions, then close and reopen the terminal so PATH changes take effect.

| Tool | Required version | Verify with |
|---|---:|---|
| Kiro CLI | 2.15.2 or later | `kiro-cli --version` |
| AWS CLI | 2.x | `aws --version` |
| Python | 3.11 or later | Windows: `py -3 --version`; Linux/macOS: `python3 --version` |
| Git (optional) | 2.x | `git --version` |

Git is only needed if you clone the repository. If you received the workshop as a ZIP download, Git is not required.

The executable is **`kiro-cli`**, not `kiro`.

## 3. Understand the v3 command

Kiro CLI 2.15.2 exposes the next-generation agent through the `--v3` chat option. Use this verified syntax:

```text
kiro-cli chat --v3
```

The workshop uses a workstation-specific main agent so its hooks call the correct Python launcher:

| Workstation | Start normal mode |
|---|---|
| Windows | `kiro-cli chat --v3 --agent windows-upgrade-windows` |
| Linux/macOS | `kiro-cli chat --v3 --agent windows-upgrade` |

Spec mode is a chat mode, not a separate `kiro-cli spec` command:

| Workstation | Start Spec mode |
|---|---|
| Windows | `kiro-cli chat --v3 --mode spec --agent windows-upgrade-windows` |
| Linux/macOS | `kiro-cli chat --v3 --mode spec --agent windows-upgrade` |

Do not use `kiro`, `kiro config`, or `kiro-cli spec`; those commands are not used by this workshop.

## 4. Open the repository

**Windows PowerShell:**

```powershell
cd C:\path\to\kiro-ws2025-workshop
```

**Linux/macOS Bash:**

```bash
cd /path/to/kiro-ws2025-workshop
```

All later Kiro commands must be run from this directory so Kiro can discover `.kiro/agents/`, steering files, skills, and the MCP servers attached to workspace agents.

## 5. Run the Kiro preflight

The preflight checks the Kiro version, v3 and Spec options, every custom-agent schema, and whether configured model IDs are available to your account.

**Windows PowerShell:**

```powershell
py -3 scripts\check_kiro_prereqs.py
```

**Linux/macOS Bash:**

```bash
python3 scripts/check_kiro_prereqs.py
```

Expected final line:

```text
Kiro workshop preflight passed
```

If it fails, follow the printed error before continuing. Available models can differ by account or change over time; the preflight detects that condition instead of silently using an unexpected model.

## 6. Verify AWS identity

Configure an AWS CLI profile before continuing. This workshop uses `default` and region `us-east-1` in its examples.

**Windows PowerShell and Linux/macOS Bash:**

```text
aws sts get-caller-identity --profile default --region us-east-1
```

Confirm that the returned account and principal are the sandbox identity you intend to use. Do not continue if it shows a production account.

## 7. Confirm the AWS regional prerequisites

**Windows PowerShell:**

```powershell
aws ssm describe-document `
  --name AWSEC2-CloneInstanceAndUpgradeWindows `
  --region us-east-1 --profile default

aws ssm get-parameter `
  --name /aws/service/ami-windows-latest/Windows_Server-2019-English-Full-Base `
  --region us-east-1 --profile default
```

**Linux/macOS Bash:**

```bash
aws ssm describe-document \
  --name AWSEC2-CloneInstanceAndUpgradeWindows \
  --region us-east-1 --profile default

aws ssm get-parameter \
  --name /aws/service/ami-windows-latest/Windows_Server-2019-English-Full-Base \
  --region us-east-1 --profile default
```

## 8. AWS permissions

The deployer needs permissions for CloudFormation, EC2, IAM, S3, Elastic Load Balancing v2, and Systems Manager. The identity that starts `AWSEC2-CloneInstanceAndUpgradeWindows` also needs its documented image, temporary-instance, volume, tagging, and instance-profile permissions.

Use a dedicated sandbox account. Kiro tool approval is an additional safety control; it does not replace IAM.

## 9. Cost and time

Budget approximately USD 15–35 for a complete run, depending on runtime and current regional prices. Each clone-upgrade can take about two hours and creates billable temporary resources. Delete lab resources when you stop the workshop.

## Non-goals

- No production data, domain joins, certificates, or external integrations.
- No proof of third-party vendor certification.
- No database production cutover.
- No guarantee that the same scripts cover all 40 real servers.

**Checkpoint:** the Kiro preflight passes, the AWS identity is the intended sandbox, both regional checks succeed, and the participant accepts the time and cost.
