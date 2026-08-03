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



## 3. Open the repository

**Windows PowerShell:**

```powershell
cd C:\path\to\kiro-workshop-file
```

**Linux/macOS Bash:**

```bash
cd /path/to/kiro-workshop-file
```

All later Kiro commands must be run from this directory.

Start a short session to confirm Kiro is working:

```text
kiro-cli chat --v3
```

Type a simple message (e.g., "hello") and confirm you get a response. To exit the session, type `/quit` or press `Ctrl+C`.

## 4. Run the Kiro preflight

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

## 5. Set AWS credentials

Your lab or Workshop Studio provides temporary credentials as environment variables. Copy them from the **AWS account access** panel into your terminal.

**Linux/macOS Bash:**

```bash
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="<from lab>"
export AWS_SECRET_ACCESS_KEY="<from lab>"
export AWS_SESSION_TOKEN="<from lab>"
```

**Windows PowerShell:**

```powershell
$env:AWS_DEFAULT_REGION="us-east-1"
$env:AWS_ACCESS_KEY_ID="<from lab>"
$env:AWS_SECRET_ACCESS_KEY="<from lab>"
$env:AWS_SESSION_TOKEN="<from lab>"
```

**Windows cmd:**

```cmd
set AWS_DEFAULT_REGION=us-east-1
set AWS_ACCESS_KEY_ID=<from lab>
set AWS_SECRET_ACCESS_KEY=<from lab>
set AWS_SESSION_TOKEN=<from lab>
```

These variables are valid for your current terminal session only. If you open a new terminal, paste them again.

## 6. Verify AWS identity

```text
aws sts get-caller-identity
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

## 7. Confirm the AWS regional prerequisites

### Check 1: Upgrade runbook exists

**Windows PowerShell:**

```powershell
aws ssm describe-document `
  --name AWSEC2-CloneInstanceAndUpgradeWindows `
  --region us-east-1
```

**Linux/macOS Bash:**

```bash
aws ssm describe-document \
  --name AWSEC2-CloneInstanceAndUpgradeWindows \
  --region us-east-1
```

Expected output:

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

### Check 2: Windows Server 2019 AMI is available

**Windows PowerShell:**

```powershell
aws ssm get-parameter `
  --name /aws/service/ami-windows-latest/Windows_Server-2019-English-Full-Base `
  --region us-east-1
```

**Linux/macOS Bash:**

```bash
aws ssm get-parameter \
  --name /aws/service/ami-windows-latest/Windows_Server-2019-English-Full-Base \
  --region us-east-1
```

Expected output:

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

If either check fails, the region may not support the upgrade runbook or the Windows Server 2019 AMI. Contact your instructor.

## 8. AWS permissions

The deployer needs permissions for CloudFormation, EC2, IAM, S3, Elastic Load Balancing v2, and Systems Manager. The identity that starts `AWSEC2-CloneInstanceAndUpgradeWindows` also needs its documented image, temporary-instance, volume, tagging, and instance-profile permissions.

Use a dedicated sandbox account. Kiro tool approval is an additional safety control; it does not replace IAM.

## 9. Cost estimation

Budget approximately USD 15–35 for a complete run, depending on runtime and current regional prices. Each clone-upgrade can take about two hours and creates billable temporary resources. Delete lab resources when you stop the workshop.

> **Disclaimer:** This estimate applies only to this workshop lab. If you implement the upgrade method in your own environment, costs will vary based on instance sizes, storage, data transfer, number of servers, and how long resources remain running. Use the [AWS Pricing Calculator](https://calculator.aws/) for your own estimate.

## Non-goals

This lab doesn't include production data, domain setup, SSL certificates, external systems, or live database cutover.

**Checkpoint:** the Kiro preflight passes, `aws sts get-caller-identity` shows the intended sandbox account, both regional checks succeed, and the participant accepts the time and cost.
