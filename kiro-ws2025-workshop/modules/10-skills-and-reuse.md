# Module 10 – Skills, reuse, and a 40-server rollout

## Inspect and activate the skill

Read `.kiro/skills/windows-upgrade/SKILL.md`. In Kiro:

```text
Activate the windows-upgrade skill. Convert this two-server evidence model into a rollout plan for 40 servers without assuming they match the lab.
```

A credible plan should add:

1. Automated inventory plus owner questionnaire.
2. Archetypes: stateless web, singleton app, database, identity-sensitive, unsupported role, unknown.
3. Per-archetype test packs and vendor-support decisions.
4. Development/test pilot, low-risk production pilot, then small waves.
5. Concurrency limits for cost and operational capacity.
6. Change windows, stop conditions, rollback ownership, and observation periods.
7. AMI/snapshot retention and cleanup policy.
8. Exception workflow for unsupported or untestable applications.

## Suggested wave gates

- **Gate A:** complete inventory, owner, RTO/RPO, dependencies.
- **Gate B:** AWS prerequisites and vendor support resolved.
- **Gate C:** baseline and backup/restore evidence pass.
- **Gate D:** upgraded clone and tests pass.
- **Gate E:** cutover architecture rehearsed.
- **Gate F:** explicit change approval.

## Kiro limitation exercise

Ask Kiro to write a refusal/qualification for a server with no source, no owner, no test oracle, a local database, and zero downtime required. The correct answer should offer discovery and architecture remediation—not claim autonomous success.

**Checkpoint:** fleet plan is archetype- and evidence-driven, not a loop over 40 instance IDs.
