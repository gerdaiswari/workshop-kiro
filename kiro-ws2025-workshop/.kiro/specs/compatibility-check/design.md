# Compatibility check design

`02_analyze_compatibility.py` consumes measured inventory, not the assumptions file. Rules are data-driven and explain their evidence. The analyzer does not assert vendor certification; it flags versions for owner/vendor confirmation using the skill's application matrix.

Report sections:

1. Server eligibility for the AWS runbook.
2. Workload presence/version and expected test coverage.
3. State, identity, and dependency risks.
4. Required remediation and owner.
5. Decision: eligible, conditional, blocked, or unsupported.

Kiro reviews the generated report, uses AWS Knowledge MCP for current AWS facts, and asks application owners to resolve vendor-specific unknowns.
