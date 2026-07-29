# Module 02 – Configure Kiro steering, agent, and permissions

## Inspect persistent context

```bash
find .kiro/steering .kiro/skills .kiro/agents -type f -maxdepth 4 -print
kiro-cli agent validate --path .kiro/agents/windows-upgrade.json
```

Steering records project facts and non-negotiable safety behavior. The skill is loaded on demand for Windows upgrade work. The custom agent allows read/code tools automatically but leaves AWS mutations approval-gated.

## Install user-owned permissions

Kiro deliberately does not load repository permission files. Review `sample-permissions.yaml`, then merge its rules into your own file:

```bash
./setup-permissions.sh --dry-run
./setup-permissions.sh
```

The setup script never overwrites an existing file; it creates a timestamped candidate for manual merge. Confirm:

```bash
cat ~/.kiro/settings/permissions.yaml
```

The rules:

- allow repository reads and deterministic checks;
- ask before deploy, upgrade, validation launch, target switching, and cleanup;
- deny common destructive AWS commands;
- allow read-only AWS Knowledge MCP calls.

## Start the workshop agent

```bash
kiro-cli chat --agent windows-upgrade
```

Try:

```text
Summarize the workshop's safety boundary and list actions requiring explicit approval. Do not call AWS.
```

Then use `/context show` and `/tools` to inspect loaded resources and trust.

**Checkpoint:** agent validates, steering is visible, and mutations are not auto-approved.
