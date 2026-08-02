# Module 07 – Validate, break, diagnose, and fix

## Learning objective
Launch Windows Server 2025 validation copies, compare them with the baseline, inject a controlled APP01 failure, and prove the tests detect and recover from it.

> **Entry gate:** return here after Modules 09, 10, and 10B only when both Module 06 upgrade scripts report `Success` and `results/upgrades/APP01.json` plus `results/upgrades/DATA01.json` contain `upgraded_ami_id`. If either upgrade is still running, continue monitoring; do not bypass the evidence.

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

This shows that Kiro can help you diagnose test failures — it correlates failed test output with the system inventory, identifies the root cause, and proposes the minimal fix, so you spend time fixing instead of searching.

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

## Transfer to your environment

- **Lab exercise:** launch isolated validation copies, compare known service/API/database checks, stop one validation-only service, prove red, repair, and prove green.
- **Reusable pattern:** validate the target OS and management plane, service recovery, business behavior, data integrity, dependencies, observability, and rollback evidence. A controlled failure demonstrates that tests can detect a regression instead of producing false confidence.
- **Adapt before reuse:** create workload-owned functional, authentication, scheduled-job, integration, performance, security, backup/restore, and reconciliation tests. Define which differences are expected and who can accept warnings. Never inject failures into a source or production target.

Adaptation prompt:

```text
Design an isolated post-upgrade test pack for my workload. Map every requirement
to objective evidence, include one safe failure proving the test can turn red,
and define which failures block promotion.
```

**Checkpoint:** the lab suite detects the controlled failure, evidence identifies the stopped service, the repair restores it, and the final comparison passes.
