# Module 09 – AWS Knowledge MCP integration

## Learning objective
Verify that the workshop custom agent loads the read-only AWS Knowledge MCP server, then use it to check current AWS documentation without calling account APIs.

## 1. Understand the configuration

Both workstation-specific main agents, plus the planner and reviewer agents, contain this agent-scoped configuration:

```json
"mcpServers": {
  "aws-knowledge-mcp-server": {
    "url": "https://knowledge-mcp.global.api.aws",
    "timeout": 120000
  }
}
```

The same agents include AWS Knowledge tools in `tools` and `allowedTools`. The server provides documentation access; it does not use your AWS account credentials or replace application testing.

## 2. Verify Kiro discovers the server

Run from the repository root.

**Windows PowerShell:**

```powershell
kiro-cli agent validate --path .kiro\agents\windows-upgrade-windows.json
kiro-cli mcp list workspace
```

**Linux/macOS Bash:**

```bash
kiro-cli agent validate --path .kiro/agents/windows-upgrade.json
kiro-cli mcp list workspace
```

The workspace listing should show `aws-knowledge-mcp-server` under both main agents (`windows-upgrade` and `windows-upgrade-windows`), `upgrade-planner`, and `upgrade-reviewer`.

## 3. Verify the tools inside chat

Start the main agent for your workstation.

**Windows:** `kiro-cli chat --v3 --agent windows-upgrade-windows`

**Linux/macOS:** `kiro-cli chat --v3 --agent windows-upgrade`

Inside chat:

```text
/tools
```

Confirm that AWS Knowledge MCP tools are present. If the server cannot initialize, check network/proxy access and restart Kiro. Do not continue this module by inventing current AWS facts.

## 4. Ask documentation questions

```text
Using AWS Knowledge MCP only, find the current documentation for
AWSEC2-CloneInstanceAndUpgradeWindows. Return supported Windows Server 2019
upgrade targets, prerequisites, exclusions, exact parameters, and source links.
Compare with .kiro/steering/aws-conventions.md and flag drift.
```

Then:

```text
Using AWS Knowledge MCP, review infra/lab.yaml for current CloudFormation and
EC2 Windows best practices. Do not call account APIs and do not edit files.
```

## Why account mutation is not enabled

Enabling authenticated AWS operation tools changes the trust boundary and requires IAM design. This workshop keeps AWS mutations in explicit Python/AWS CLI workflows with confirmations and saved evidence. Documentation retrieval improves currency; it does not replace deterministic compatibility tests or application-owner acceptance.

**Checkpoint:** `kiro-cli mcp list workspace` shows the agent-scoped server, `/tools` shows AWS Knowledge tools, and Kiro answers with current AWS source links without invoking account APIs.
