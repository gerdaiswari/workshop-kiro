# Module 09 – MCP integration

The project configures only the remote, unauthenticated, read-only AWS Knowledge MCP server:

```json
{
  "mcpServers": {
    "aws-knowledge-mcp-server": {
      "url": "https://knowledge-mcp.global.api.aws",
      "type": "http",
      "disabled": false
    }
  }
}
```

Check it:

```bash
kiro-cli mcp list workspace
kiro-cli mcp status --name aws-knowledge-mcp-server
```

In Kiro, ask:

```text
Using AWS Knowledge MCP only, find the current documentation for AWSEC2-CloneInstanceAndUpgradeWindows. Return supported 2019 upgrade targets, prerequisites, exclusions, exact parameters, and source links. Compare with .kiro/steering/aws-conventions.md and flag drift.
```

Then:

```text
Using AWS Knowledge MCP, review infra/lab.yaml for current CloudFormation and EC2 Windows best practices. Do not call account APIs and do not edit files.
```

## Why account mutation is not enabled by default

The managed AWS MCP Server can expose authenticated AWS operations, but enabling it changes the trust boundary and requires IAM design. This workshop uses AWS CLI scripts whose commands, inputs, outputs, and permission prompts are easy to inspect. An advanced class can add the managed AWS MCP Server with a read-only role first, then separately approve specific write tools.

MCP documentation retrieval improves currency; it does not replace deterministic compatibility tests or application-owner acceptance.

**Checkpoint:** Kiro retrieves current AWS facts through MCP and detects no unexplained drift.
