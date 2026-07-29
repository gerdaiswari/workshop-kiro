# Module 11 – Cleanup

Cleanup is destructive and intentionally separate from the upgrade flow.

## Review resources

```bash
./scripts/08_cleanup.sh --plan \
  --region ap-southeast-1 --profile default \
  --stack-name kiro-ws2025-lab
```

The plan includes:

- Validation instances recorded in workshop state.
- Retained pre-upgrade and upgraded AMIs and their snapshots.
- CloudFormation stack resources.
- Workshop artifact bucket and objects.

## Execute after explicit approval

The workshop Kiro agent and hook deny destructive commands. Run cleanup manually outside the agent after reviewing IDs:

```bash
./scripts/08_cleanup.sh --execute \
  --region ap-southeast-1 --profile default \
  --stack-name kiro-ws2025-lab
```

Type the stack name to confirm. The script terminates only instances and deregisters only AMIs recorded in this workshop's `results/` state and carrying the project tag where tags are available. It then deletes the stack and artifact bucket.

## Verify

```bash
aws cloudformation describe-stacks --stack-name kiro-ws2025-lab \
  --region ap-southeast-1 --profile default
```

A `ValidationError` saying the stack does not exist is expected. Also inspect EC2 AMIs/snapshots with the project tag to ensure no retained charges remain.

Preserve non-secret JSON/Markdown evidence if required, but never retain generated database passwords or dumps.

**Checkpoint:** stack, validation instances, retained AMIs/snapshots, ALB, EBS, and artifact bucket are removed.
