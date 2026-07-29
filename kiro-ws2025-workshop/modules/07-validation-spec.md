# Module 07 – Validate, break, diagnose, and fix

## Launch validation copies

```bash
python3 scripts/05_launch_validation.py --server APP01 \
  --region ap-southeast-1 --profile default --stack-name kiro-ws2025-lab
python3 scripts/05_launch_validation.py --server DATA01 \
  --region ap-southeast-1 --profile default --stack-name kiro-ws2025-lab
```

Each command asks for approval, launches from the recorded upgraded AMI, requires IMDSv2, waits for EC2 checks and SSM Online, and records the instance ID.

## Run post-upgrade tests

```bash
python3 scripts/03_run_tests.py --phase post \
  --region ap-southeast-1 --profile default --stack-name kiro-ws2025-lab
python3 scripts/06_compare_results.py
```

Review `results/tests/comparison.json` and `.md`. Windows version intentionally changes; service/API/data behavior should not regress.

## Inject a realistic validation failure

```bash
python3 scripts/failure_scenario.py --action inject \
  --region ap-southeast-1 --profile default
python3 scripts/03_run_tests.py --phase post \
  --region ap-southeast-1 --profile default --stack-name kiro-ws2025-lab
```

The script stops `KiroNext` only after verifying the target is tagged `Role=VAL-APP01`. The Next.js checks must fail.

Ask Kiro:

```text
Use the failed post-test evidence and inventory to diagnose the VAL-APP01 issue. Propose the smallest reversible fix and verification. Do not change source APP01.
```

Repair and verify:

```bash
python3 scripts/failure_scenario.py --action repair \
  --region ap-southeast-1 --profile default
python3 scripts/03_run_tests.py --phase post \
  --region ap-southeast-1 --profile default --stack-name kiro-ws2025-lab
python3 scripts/06_compare_results.py
```

**Checkpoint:** failure is detected, attributed, repaired, and followed by a clean comparison.
