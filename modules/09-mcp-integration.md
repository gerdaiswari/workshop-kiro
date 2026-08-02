# Module 09 – Add AWS Knowledge MCP to your agent

## Learning objective

Configure an MCP server yourself, expose its tools to the agent you created, verify discovery, and use it for current AWS documentation without calling your AWS account APIs.

> **Workshop navigation:** Module 06 upgrades are running → **Module 09 (you are here)** → Module 10 → Module 10B → return to Module 07 after both upgrades succeed.
>
> Complete this module in a third terminal while the two Module 06 upgrade terminals continue polling. Do not stop or reuse those terminals.

## 1. Understand why MCP is needed

A language model may have stale AWS product knowledge. The read-only AWS Knowledge MCP server lets Kiro retrieve current AWS documentation and source links.

In this workshop MCP is used for documentation only. It does not authenticate to your AWS account, inspect your instances, or perform upgrades.

This shows that Kiro can help you access current AWS documentation on demand — instead of searching docs manually, Kiro retrieves the latest information and source links directly in your conversation, so your decisions are based on current facts rather than stale training data.

## 2. Add the MCP server to your agent

Start plain Kiro:

```text
kiro-cli chat --v3
```

Ask Kiro to update `.kiro/agents/my-windows-upgrade.json` with these three changes:

1. Add `"@aws-knowledge-mcp-server/*"` to `tools`.
2. Add `"@aws-knowledge-mcp-server/*"` to `allowedTools` because this server is read-only documentation access.
3. Add this top-level object:

```json
"mcpServers": {
  "aws-knowledge-mcp-server": {
    "url": "https://knowledge-mcp.global.api.aws",
    "timeout": 120000
  }
}
```

Review the URL and tool name before approving the edit. MCP servers are code/data trust boundaries; do not add an unknown server merely because a prompt suggests it.

## 3. Validate the updated agent

Exit Kiro, then run the command for your workstation.

**Windows PowerShell:**

```powershell
kiro-cli agent validate --path .kiro\agents\my-windows-upgrade.json
```

**Linux/macOS Bash:**

```bash
kiro-cli agent validate --path .kiro/agents/my-windows-upgrade.json
```

A schema-valid agent does not prove the network endpoint is reachable; discovery is the next check.

## 4. Verify MCP discovery

```text
kiro-cli mcp list workspace
```

Expected section:

```text
my-windows-upgrade
  • aws-knowledge-mcp-server
```

If it is missing, confirm that:

- Kiro was started from the repository root.
- The `mcpServers` object is top-level in the agent JSON.
- The server name exactly matches the tool prefix.
- Your proxy/firewall permits HTTPS access to `knowledge-mcp.global.api.aws`.

## 5. Verify MCP tools in chat

Start the agent you created:

```text
kiro-cli chat --v3 --agent my-windows-upgrade
```

Inside chat:

```text
/tools
```

Confirm that AWS Knowledge tools appear alongside the local tools you added earlier.

## 6. Use MCP for an upgrade documentation check

Ask:

```text
Using AWS Knowledge MCP only, find the current AWS documentation for
AWSEC2-CloneInstanceAndUpgradeWindows. Return supported source and target
operating systems, prerequisites, exclusions, exact parameters, and source links.
Do not call account APIs and do not edit files.
```

Then ask:

```text
Using AWS Knowledge MCP, review infra/lab.yaml against current EC2 Windows,
CloudFormation, Systems Manager, and IMDS security guidance. Separate documented
requirements from recommendations and include source links. Do not edit files.
```

MCP improves documentation currency; it does not prove application compatibility or replace deterministic tests.

This shows that Kiro can help you audit your infrastructure against current best practices — it cross-references your CloudFormation templates with live AWS documentation and separates hard requirements from recommendations, with source links you can verify.

## 7. Compare with the reference configuration

After your MCP exercise works, compare your agent with the reference agents:

- `.kiro/agents/windows-upgrade.md` (orchestrator — has MCP for documentation lookups)
- `.kiro/agents/upgrade-reviewer.md` (reviewer — has MCP because reviewing requires current docs)
- `.kiro/agents/upgrade-executor.md` (executor — no MCP, it only runs scripts)

Notice which agents receive documentation access and why the execution-focused agent does not need it.

## Why authenticated mutation MCP is not enabled

An MCP server that operates on your AWS account would change the trust boundary and require separate IAM, approval, logging, and server-supply-chain review. This workshop keeps AWS mutations in explicit Python/AWS CLI workflows with confirmations and saved evidence.

**Checkpoint:** you added `mcpServers` and the MCP tool prefix to your own agent, validation passed, `kiro-cli mcp list workspace` discovered the server, `/tools` showed it, and your response included current AWS source links without account API calls.
