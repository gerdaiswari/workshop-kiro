#!/usr/bin/env python3
"""Verify Kiro CLI prerequisites used by this workshop."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MINIMUM_VERSION = (2, 15, 2)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    executable = shutil.which("kiro-cli")
    if not executable:
        fail("kiro-cli was not found in PATH. Install Kiro CLI, reopen the terminal, and retry.")

    version_result = run(executable, "--version")
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_result.stdout + version_result.stderr)
    if version_result.returncode or not match:
        fail("Could not read the Kiro CLI version with 'kiro-cli --version'.")
    version = tuple(int(part) for part in match.groups())
    if version < MINIMUM_VERSION:
        fail(f"Kiro CLI {'.'.join(match.groups())} is installed; this workshop requires 2.15.2 or later.")

    chat_help = run(executable, "chat", "--help")
    for option in ("--v3", "--mode", "--list-models", "--agent"):
        if option not in chat_help.stdout:
            fail(f"Installed Kiro CLI does not expose required chat option {option}.")

    models_result = run(executable, "chat", "--list-models", "--format", "json")
    if models_result.returncode:
        fail("Could not list models. Sign in to Kiro CLI and retry.")
    try:
        model_document = json.loads(models_result.stdout)
        available_models = {item["model_id"] for item in model_document["models"]}
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        fail(f"Could not parse 'kiro-cli chat --list-models' output: {exc}")

    agent_files = sorted((ROOT / ".kiro" / "agents").glob("*.json"))
    if not agent_files:
        fail("No workspace agents were found under .kiro/agents/.")
    for path in agent_files:
        validation = run(executable, "agent", "validate", "--path", str(path))
        if validation.returncode:
            fail(f"Agent validation failed for {path.name}:\n{validation.stdout}{validation.stderr}")
        config = json.loads(path.read_text(encoding="utf-8"))
        configured_model = config.get("model")
        if configured_model and configured_model not in available_models:
            fail(
                f"Agent {config.get('name', path.stem)} requests unavailable model {configured_model!r}. "
                "Run 'kiro-cli chat --list-models' and update the agent model."
            )
        print(f"PASS agent: {path.stem}" + (f" (model: {configured_model})" if configured_model else " (default model)"))

    settings = run(executable, "settings", "list", "--all")
    if settings.returncode or "chat.enableSubagent" not in settings.stdout:
        fail("This Kiro CLI installation does not expose the chat.enableSubagent setting.")

    print(f"PASS Kiro CLI version: {'.'.join(match.groups())}")
    print("PASS v3 and Spec-mode options are available")
    print(f"PASS available models: {len(available_models)}")
    print("Kiro workshop preflight passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
