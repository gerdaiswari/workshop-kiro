# Module 03 – Inventory with a Kiro Spec

## Review or recreate the Spec

The repository includes an instructor-approved Spec. Resume it:

```text
/spec inventory-assessment
```

To practice from scratch, use a different name:

```text
/spec new participant-inventory
```

Description:

```text
Collect read-only AWS and Windows facts for APP01 and DATA01 through SSM, redact secrets, identify unsupported Windows roles, and write normalized JSON with per-server errors.
```

Review requirements, design, and tasks before execution. Specs live in `.kiro/specs/<name>/` and remain editable.

## Collect measured inventory

```bash
python3 scripts/01_collect_inventory.py \
  --region ap-southeast-1 --profile default \
  --stack-name kiro-ws2025-lab
```

Review:

```bash
python3 -m json.tool results/inventory/inventory.json | less
```

Ask Kiro:

```text
Compare results/inventory/inventory.json with inventory/assumed-inventory.yaml. List discrepancies, unknown dependencies, stateful components, unsupported roles, and missing test oracles. Do not modify either file.
```

Important: program and service discovery is evidence, not ownership or vendor support. Unknowns stay unknown until an owner resolves them.

**Checkpoint:** both servers collected successfully; workload/services/ports match the lab; no secret values are present.
