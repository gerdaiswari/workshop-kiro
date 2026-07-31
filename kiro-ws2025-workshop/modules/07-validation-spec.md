# Module 07 – Validate, break, diagnose, and fix

## Learning objective
Launch Windows Server 2025 validation copies, compare them with the baseline, inject a controlled APP01 failure, and prove the tests detect and recover from it.

## 1. Launch validation copies

Each command requires approval, launches from a recorded upgraded AMI, enforces IMDSv2, waits for EC2 and SSM readiness, and records the new instance ID.

**Windows PowerShell:**

```powershell
py -3 scripts\05_launch_validation.py --server APP01 `
  --region us-east-1 --stack-name kiro-ws2025-lab
py -3 scripts\05_launch_validation.py --server DATA01 `
  --region us-east-1 --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/05_launch_validation.py --server APP01 \
  --region us-east-1 --stack-name kiro-ws2025-lab
python3 scripts/05_launch_validation.py --server DATA01 \
  --region us-east-1 --stack-name kiro-ws2025-lab
```

## 2. Run post-upgrade tests and compare

**Windows PowerShell:**

```powershell
py -3 scripts\03_run_tests.py --phase post `
  --region us-east-1 --stack-name kiro-ws2025-lab
py -3 scripts\06_compare_results.py
```

**Linux/macOS Bash:**

```bash
python3 scripts/03_run_tests.py --phase post \
  --region us-east-1 --stack-name kiro-ws2025-lab
python3 scripts/06_compare_results.py
```

Review `results/tests/comparison.json` and `results/tests/comparison.md`. The Windows version should change; application, service, API, and data behavior should not regress.

## 3. Inject a controlled validation-only failure

The injection script first verifies that the target is tagged `Role=VAL-APP01`; it does not target source APP01.

**Windows PowerShell:**

```powershell
py -3 scripts\failure_scenario.py --action inject `
  --region us-east-1
py -3 scripts\03_run_tests.py --phase post `
  --region us-east-1 --stack-name kiro-ws2025-lab
```

**Linux/macOS Bash:**

```bash
python3 scripts/failure_scenario.py --action inject \
  --region us-east-1
python3 scripts/03_run_tests.py --phase post \
  --region us-east-1 --stack-name kiro-ws2025-lab
```

The Next.js checks should now fail.

Start Kiro:

Start the agent you created:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Ask:

```text
Use the failed post-test evidence and inventory to diagnose the VAL-APP01
issue. Propose the smallest reversible fix and its verification steps.
Do not change source APP01 and do not call AWS.
```

## 4. Repair and verify

**Windows PowerShell:**

```powershell
py -3 scripts\failure_scenario.py --action repair `
  --region us-east-1
py -3 scripts\03_run_tests.py --phase post `
  --region us-east-1 --stack-name kiro-ws2025-lab
py -3 scripts\06_compare_results.py
```

**Linux/macOS Bash:**

```bash
python3 scripts/failure_scenario.py --action repair \
  --region us-east-1
python3 scripts/03_run_tests.py --phase post \
  --region us-east-1 --stack-name kiro-ws2025-lab
python3 scripts/06_compare_results.py
```

**Checkpoint:** the test suite detects the controlled failure, evidence identifies the stopped service, the repair restores it, and the final comparison passes.
