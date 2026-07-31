# Module 10 – Create a reusable skill and plan fleet rollout

## Learning objective

Create a Kiro skill yourself, attach it to your custom agent, activate it in a real planning task, and understand how a skill differs from steering and an agent prompt.

## 1. Understand the difference

| Feature | Scope | Best use |
|---|---|---|
| Steering | All workspace sessions | Durable project facts, conventions, and safety rules |
| Agent prompt | One named agent | Role, behavior, tool boundaries, and approval posture |
| Skill | Reusable procedure loaded when relevant | Step-by-step domain workflow and reference material |

A skill should be reusable across repositories and workloads. Do not put account-specific credentials, instance IDs, or temporary state in it.

## 2. Create your own skill

Start plain Kiro:

```text
kiro-cli chat --v3
```

Ask it to create `.kiro/skills/participant-windows-upgrade/SKILL.md` with exactly this content:

```markdown
---
name: participant-windows-upgrade
description: Participant-created procedure for assessing and validating Windows Server EC2 clone upgrades. Use for inventory, compatibility, test design, validation, and rollback planning.
---

# Participant Windows upgrade procedure

## Workflow

1. Collect measured inventory; label unknown facts explicitly.
2. Classify the workload as stateless, stateful, identity-sensitive, unsupported, or unknown.
3. Confirm AWS technical prerequisites and application vendor support separately.
4. Capture baseline application and data evidence before upgrade.
5. Create native backups for stateful services and define a tested restore path.
6. Clone-upgrade; never describe the workflow as upgrading the production source in place.
7. Launch an isolated validation instance from the upgraded AMI.
8. Compare baseline and post-upgrade results; unexplained regressions block promotion.
9. Define cutover and rollback according to state, dependencies, RTO, and RPO.
10. Require explicit approval before AWS mutations.

## Required outputs

- Measured inventory and compatibility decision.
- Baseline and post-upgrade evidence.
- Upgrade execution ID and AMI IDs.
- Cutover, rollback, owner, and approval record.
```

Review the front matter and procedure before approving the write.

## 3. Attach the skill to your agent

Ask plain Kiro to add this entry to the `resources` array in `.kiro/agents/my-windows-upgrade.json`:

```json
"skill://.kiro/skills/**/SKILL.md"
```

Keep the existing README and steering resources. Validate the agent after the edit.

**Windows PowerShell:**

```powershell
kiro-cli agent validate --path .kiro\agents\my-windows-upgrade.json
```

**Linux/macOS Bash:**

```bash
kiro-cli agent validate --path .kiro/agents/my-windows-upgrade.json
```

## 4. Activate the skill

Start your agent:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Ask:

```text
Activate the participant-windows-upgrade skill. Convert this two-server evidence
model into a rollout plan for 40 servers without assuming they match the lab.
Show which parts of the answer came from the skill and which require new discovery.
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

## 5. Suggested wave gates

- **Gate A:** complete inventory, owner, RTO/RPO, dependencies.
- **Gate B:** AWS prerequisites and vendor support resolved.
- **Gate C:** baseline and backup/restore evidence pass.
- **Gate D:** upgraded clone and tests pass.
- **Gate E:** cutover architecture rehearsed.
- **Gate F:** explicit change approval.

## 6. Compare with the reference skill

Now compare your skill with:

- `.kiro/skills/windows-upgrade/SKILL.md`
- `.kiro/skills/windows-upgrade/references/app-matrix.md`
- `.kiro/skills/windows-upgrade/references/known-issues.md`

The reference version is longer because it includes mandatory outputs and reusable compatibility references. Improve your skill only when a rule is broadly reusable; keep workload-specific facts in inventory or steering.

## 7. Kiro limitation exercise

Ask your agent:

```text
A server has no source code, no application owner, no test oracle, a local
unknown database, and a zero-downtime requirement. Apply the skill and decide
whether it is ready to upgrade.
```

The correct response should identify blockers and propose discovery/architecture work—not claim autonomous success.

**Checkpoint:** you created a valid skill with front matter, attached it through `resources`, activated it, used it for fleet planning, and can explain how skills differ from steering and agent prompts.
