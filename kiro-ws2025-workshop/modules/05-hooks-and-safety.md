# Module 05 – Hooks, approvals, and baseline tests

## Inspect hooks

```bash
cat .kiro/hooks/safety-gates.json
```

The command hook receives JSON on stdin. Exit code 2 blocks `PreToolUse`. Test the hook directly:

```bash
printf '%s' '{"tool_input":{"command":"aws ec2 terminate-instances --instance-ids i-example"}}' \
  | python3 scripts/hooks/block_destructive.py
echo $?
```

Expected exit code: `2`. A describe command should return `0`.

The `PostFileSave` hook runs the quick static validator after Python, PowerShell, or shell automation changes. The `PreTaskExec` hook adds a safety/evidence reminder; permissions—not an agent reminder—provide the actual user approval boundary.

## Capture baseline tests

```bash
python3 scripts/03_run_tests.py \
  --phase baseline \
  --region ap-southeast-1 --profile default \
  --stack-name kiro-ws2025-lab
```

Results are written under `results/tests/baseline/`. Review stable check IDs, values, and evidence. Baseline must pass before upgrade.

## Prepare stateful recovery evidence

```bash
python3 scripts/03_run_tests.py \
  --phase backup-data \
  --region ap-southeast-1 --profile default \
  --stack-name kiro-ws2025-lab
```

Backups remain on DATA01 for this synthetic lab. In production, copy encrypted backups to a controlled repository and prove restore independently.

**Checkpoint:** hook block test succeeds, APP01/DATA01 baseline passes, and native backup checks pass.
