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
| Python | 3.9 or later | Windows: `py -3 --version`; Linux/macOS: `python3 --version` |
| Git (optional) | 2.x | `git --version` |

Git is only needed if you clone the repository. If you received the workshop as a ZIP download, Git is not required.

The executable is **`kiro-cli`**, not `kiro`.

## 3. Two ways to work: Vibe mode and Spec mode

Kiro has two modes you'll use in this workshop:

| Mode | What it does | When to use |
|---|---|---|
| **Vibe** (default) | You chat freely, Kiro executes tasks directly | Running scripts, exploring, asking questions, fixing issues |
| **Spec** | Kiro creates a structured plan (requirements → design → tasks) before acting | Planning upgrades, designing test strategies, defining change scope |

Start Vibe mode:

```text
kiro-cli chat --v3
```

Start Spec mode:

```text
kiro-cli chat --v3 --mode spec
```

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

## 6. Configure AWS CLI credentials

Your credentials come from the lab or workshop studio environment provided by your instructor. Configure the AWS CLI `default` profile:

```text
aws configure --profile default
```

Enter the values provided:

```
AWS Access Key ID [None]: <from lab/workshop studio>
AWS Secret Access Key [None]: <from lab/workshop studio>
Default region name [None]: us-east-1
Default output format [None]: json
```

If your lab uses temporary session credentials, also set the session token:

```text
aws configure set aws_session_token <token> --profile default
```

## 7. Verify AWS identity

```text
aws sts get-caller-identity --profile default --region us-east-1
```

Expected output (values will differ):

```json
{
    "UserId": "AROAEXAMPLEID:workshop-user",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/WorkshopRole/workshop-user"
}
```

Confirm the account number matches your lab/sandbox account. Do not continue if it shows a production account.

## 8. Confirm the AWS regional prerequisites

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

Expected output for the document check:

```json
{
    "Document": {
        "Name": "AWSEC2-CloneInstanceAndUpgradeWindows",
        "DocumentType": "Automation",
        "Status": "Active",
        ...
    }
}
```

Expected output for the AMI parameter:

```json
{
    "Parameter": {
        "Name": "/aws/service/ami-windows-latest/Windows_Server-2019-English-Full-Base",
        "Type": "String",
        "Value": "ami-0xxxxxxxxxxxxxxxxx",
        ...
    }
}
```

If either command fails, the region may not support the upgrade runbook or the Windows Server 2019 AMI. Contact your instructor.

## 9. AWS permissions

The deployer needs permissions for CloudFormation, EC2, IAM, S3, Elastic Load Balancing v2, and Systems Manager. The identity that starts `AWSEC2-CloneInstanceAndUpgradeWindows` also needs its documented image, temporary-instance, volume, tagging, and instance-profile permissions.

Use a dedicated sandbox account. Kiro tool approval is an additional safety control; it does not replace IAM.

## 10. Cost estimation

Budget approximately USD 15–35 for a complete run, depending on runtime and current regional prices. Each clone-upgrade can take about two hours and creates billable temporary resources. Delete lab resources when you stop the workshop.

> **Disclaimer:** This estimate applies only to this workshop lab. If you implement the upgrade method in your own environment, costs will vary based on instance sizes, storage, data transfer, number of servers, and how long resources remain running. Use the [AWS Pricing Calculator](https://calculator.aws/) for your own estimate.

## Non-goals

- No production data, domain joins, certificates, or external integrations.
- No proof of third-party vendor certification.
- No database production cutover.

**Checkpoint:** the Kiro preflight passes, `aws sts get-caller-identity` shows the intended sandbox account, both regional checks succeed, and the participant accepts the time and cost.
