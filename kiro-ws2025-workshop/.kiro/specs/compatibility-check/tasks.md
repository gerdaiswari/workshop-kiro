# Compatibility check tasks

- [ ] 1. Confirm measured inventory is complete and current.
- [ ] 2. Run `python3 scripts/02_analyze_compatibility.py`.
- [ ] 3. Use AWS Knowledge MCP to re-check the runbook path, prerequisites, exclusions, and parameters.
- [ ] 4. Map every discovered workload to a mandatory test and an accountable owner.
- [ ] 5. Resolve or explicitly accept each `unknown`; never auto-convert unknown to pass.
- [ ] 6. Block upgrade execution if the report contains any blocker.
