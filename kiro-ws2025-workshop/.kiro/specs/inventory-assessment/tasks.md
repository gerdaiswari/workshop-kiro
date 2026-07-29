# Inventory assessment tasks

- [ ] 1. Run repository static validation and verify AWS identity/region.
- [ ] 2. Verify APP01 and DATA01 are `Online` in Systems Manager.
- [ ] 3. Run `python3 scripts/01_collect_inventory.py --region <region> --profile <profile>`.
- [ ] 4. Compare measured roles, ports, runtimes, and volumes with `inventory/assumed-inventory.yaml`.
- [ ] 5. Record discrepancies and unknown ownership/dependencies in the inventory result.
- [ ] 6. Confirm the inventory contains no secret values and mark the Spec complete only when both servers succeeded.
