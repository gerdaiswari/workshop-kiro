# Module 10 – Create a reusable skill and plan fleet rollout

## Learning objective

Create a Kiro skill yourself, attach it to your custom agent, activate it in a real planning task, and understand how a skill differs from steering and an agent prompt.

## Why this matters

By now you've used three different ways to give Kiro persistent knowledge: steering (Module 02, durable project facts and rules), an agent prompt (Module 02, one agent's role and behavior), and now a skill — a reusable, step-by-step procedure that Kiro loads only when it's relevant to the task at hand. The distinction matters because each is meant for different content: steering holds facts about *this* project, an agent prompt defines *one agent's* personality and boundaries, and a skill holds a *portable* workflow you could copy into a completely different repository and it would still make sense. You'll build a skill that encodes the Windows-upgrade procedure itself, then use it to scale this workshop's two-server exercise into a rollout plan for 40 servers.

> **Workshop navigation:** Module 06 upgrades are running → Module 09 → **Module 10 (you are here)** → Module 10B → return to Module 07 after both upgrades succeed.
>
> Complete this module in the third terminal while the original upgrade terminals continue polling.

## 1. Understand the difference

| Feature | Scope | Best use |
|---|---|---|
| Steering | All workspace sessions | Durable project facts, conventions, and safety rules |
| Agent prompt | One named agent | Role, behavior, tool boundaries, and approval posture |
| Skill | Reusable procedure loaded when relevant | Step-by-step domain workflow and reference material |

A skill should be reusable across repositories and workloads — that's the test for whether something belongs in a skill versus steering. Do not put account-specific credentials, instance IDs, or temporary state in it; those belong in steering or in your inventory files, not in a procedure meant to travel with you to other projects.

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

Review the front matter and procedure before approving the write. The `description` field in the front matter is what Kiro uses to decide when this skill is relevant — it's what gets matched against your prompt, so it needs to clearly state what the skill is for.

## 3. Attach the skill to your agent

Ask plain Kiro to add your own skill to the `resources` array in `.kiro/agents/my-windows-upgrade.json` — this is what makes the skill available to your agent at all; without it, Kiro doesn't know the skill file exists:

```json
"skill://.kiro/skills/participant-windows-upgrade/SKILL.md"
```

Point at your own skill file by name rather than a wildcard, so your intent is explicit and you can see exactly which skill is attached just by reading the agent JSON. Keep the existing README and steering resources. Validate the agent after the edit.

**Windows PowerShell:**

```powershell
kiro-cli agent validate --path .kiro\agents\my-windows-upgrade.json
```

**Linux/macOS Bash:**

```bash
kiro-cli agent validate --path .kiro/agents/my-windows-upgrade.json
```

Your skill and the supplied `windows-upgrade` skill can coexist. They have different folder names, so they never overwrite each other. Kiro may see both skills' short descriptions when deciding what's relevant, but a skill's full content only loads when it is actually activated for a given task, and Kiro uses whichever one your prompt asks for. Two skills are alternatives, not a conflict — it's no different from having two reference documents on a shelf.

## 4. Activate the skill

Start your agent:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Ask — notice the prompt explicitly says "Activate," which tells Kiro to load the skill's full content into context for this task, rather than just knowing it exists:

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

This shows that Kiro can help you scale a proven procedure into a fleet plan — it follows the skill's workflow steps, identifies what changes at scale (waves, gates, concurrency, exceptions), and produces a structured rollout plan instead of a flat to-do list.

## 5. Suggested wave gates

- **Gate A:** complete inventory, owner, RTO/RPO, dependencies.
- **Gate B:** AWS prerequisites and vendor support resolved.
- **Gate C:** baseline and backup/restore evidence pass.
- **Gate D:** upgraded clone and tests pass.
- **Gate E:** cutover architecture rehearsed.
- **Gate F:** explicit change approval.

## 6. Compare with the reference skill

Comparing is a read-only study step. You do not merge, overwrite, or delete anything—your `participant-windows-upgrade` skill and the supplied `windows-upgrade` skill stay in separate folders.

Ask your agent to compare them for you:

```text
Compare .kiro/skills/participant-windows-upgrade/SKILL.md with
.kiro/skills/windows-upgrade/SKILL.md and its reference notes. List what the
reference covers that mine does not, and which of those additions are broadly
reusable versus lab-specific. Do not edit either file.
```

Or view the difference directly in your terminal:

```text
git diff --no-index .kiro/skills/participant-windows-upgrade/SKILL.md .kiro/skills/windows-upgrade/SKILL.md
```

The reference is longer because it adds mandatory outputs and reusable compatibility notes:

- `.kiro/skills/windows-upgrade/SKILL.md`
- `.kiro/skills/windows-upgrade/references/app-matrix.md`
- `.kiro/skills/windows-upgrade/references/known-issues.md`

Improve your own skill only when a rule is broadly reusable. Keep workload-specific facts in inventory or steering, not in the skill.

## 7. Kiro limitation exercise

Ask your agent:

```text
A server has no source code, no application owner, no test oracle, a local
unknown database, and a zero-downtime requirement. Apply the skill and decide
whether it is ready to upgrade.
```

The correct response should identify blockers and propose discovery/architecture work—not claim autonomous success.

This shows that Kiro can help you identify what's NOT ready — it applies the procedure honestly, flags missing prerequisites as blockers, and tells you what discovery work is needed before proceeding, instead of giving you false confidence.

**Checkpoint:** you created a valid skill with front matter, attached it through `resources`, activated it, used it for fleet planning, and can explain how skills differ from steering and agent prompts.

## Further reading

For guidance on reusing this workshop's approach in production, see the [Kiro context and reuse guide](../docs/kiro-context-and-reuse.md).
