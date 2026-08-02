#!/usr/bin/env python3
"""Kiro PreToolUse hook: reject destructive shell commands.

Hook context is JSON on stdin. Kiro CLI v3 blocks a preToolUse command when
this program exits with status 2 and returns stderr to the model.
"""
from __future__ import annotations

import json
import re
import sys

BLOCKED = re.compile(
    r"(?:aws\s+(?:ec2\s+(?:terminate-instances|delete-snapshot|deregister-image)|"
    r"cloudformation\s+delete-stack|ssm\s+delete-)|rm\s+-rf|"
    r"Remove-Item\b.*\b-Recurse)",
    re.IGNORECASE | re.DOTALL,
)


def extract_command(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("command", "cli_command", "input", "tool_input"):
            if key in value:
                found = extract_command(value[key])
                if found:
                    return found
        return " ".join(extract_command(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(extract_command(item) for item in value)
    return ""


def main() -> int:
    raw = sys.stdin.read()
    try:
        context = json.loads(raw or "{}")
    except json.JSONDecodeError:
        context = {"raw": raw}
    command = extract_command(context)
    match = BLOCKED.search(command)
    if match:
        print(
            f"BLOCKED by workshop safety hook: {match.group(0)!r}. "
            "Destructive cleanup must be a separately approved manual task.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
