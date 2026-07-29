#!/usr/bin/env python3
"""Offline structural and syntax validation for the workshop repository."""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    "README.md", "infra/lab.yaml", "bootstrap/app01.ps1", "bootstrap/data01.ps1",
    "scripts/00_deploy.sh", "scripts/01_collect_inventory.py", "scripts/02_analyze_compatibility.py",
    "scripts/03_run_tests.py", "scripts/04_start_upgrade.py", "scripts/05_launch_validation.py",
    "scripts/06_compare_results.py", "scripts/07_app_cutover.py", "scripts/08_cleanup.sh",
    ".kiro/agents/windows-upgrade.json", ".kiro/hooks/safety-gates.json",
    ".kiro/settings/mcp.json", ".kiro/skills/windows-upgrade/SKILL.md",
    "inventory/assumed-inventory.yaml",
]
VALID_HOOK_TRIGGERS = {
    "SessionStart", "Stop", "PreToolUse", "PostToolUse", "PreTaskExec", "PostTaskExec",
    "UserPromptSubmit", "PostFileCreate", "PostFileSave", "PostFileDelete", "Manual",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    for path in ROOT.rglob("*.json"):
        if "results" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")

    for path in ROOT.rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"invalid Python {path.relative_to(ROOT)}: {exc}")

    try:
        ET.parse(ROOT / "apps/app01/spring/pom.xml")
    except Exception as exc:
        errors.append(f"invalid Maven XML: {exc}")

    shell_files = [ROOT / "setup-permissions.sh", *ROOT.glob("scripts/*.sh")]
    for path in shell_files:
        result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
        if result.returncode:
            errors.append(f"invalid shell {path.relative_to(ROOT)}: {result.stderr.strip()}")

    for path in [ROOT / "infra/lab.yaml", ROOT / "inventory/assumed-inventory.yaml", ROOT / "sample-permissions.yaml"]:
        text = path.read_text(encoding="utf-8")
        if "\t" in text:
            errors.append(f"tab character in YAML {path.relative_to(ROOT)}")

    hooks = json.loads((ROOT / ".kiro/hooks/safety-gates.json").read_text(encoding="utf-8"))
    if hooks.get("version") != "v1":
        errors.append("hook schema version must be v1")
    for hook in hooks.get("hooks", []):
        if hook.get("trigger") not in VALID_HOOK_TRIGGERS:
            errors.append(f"invalid hook trigger: {hook.get('trigger')}")
        if hook.get("action", {}).get("type") not in {"command", "agent"}:
            errors.append(f"invalid hook action: {hook.get('name')}")

    mcp_text = (ROOT / ".kiro/settings/mcp.json").read_text(encoding="utf-8")
    if "@latest" in mcp_text:
        errors.append("project MCP config must not install @latest dependencies")

    for spec in (ROOT / ".kiro/specs").iterdir():
        if spec.is_dir():
            for name in ("requirements.md", "design.md", "tasks.md"):
                if not (spec / name).is_file():
                    errors.append(f"incomplete spec {spec.name}: missing {name}")

    secret_pattern = re.compile(r"AKIA[0-9A-Z]{16}|aws_secret_access_key\s*[:=]", re.IGNORECASE)
    for path in ROOT.rglob("*"):
        if not path.is_file() or "results" in path.parts or path.suffix.lower() in {".png", ".jpg", ".zip"}:
            continue
        try: text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError: continue
        if secret_pattern.search(text):
            errors.append(f"possible AWS secret in {path.relative_to(ROOT)}")

    if not args.quick:
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for path in ROOT.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for target in link_pattern.findall(text):
                target = target.split("#", 1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    errors.append(f"broken local link in {path.relative_to(ROOT)}: {target}")

        pwsh = shutil.which("pwsh")
        if pwsh:
            for path in ROOT.rglob("*.ps1"):
                escaped_path = str(path).replace("'", "''")
                command = (
                    "$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile("
                    f"'{escaped_path}',[ref]$t,[ref]$e)|Out-Null;"
                    "if($e.Count){$e|ForEach-Object{[Console]::Error.WriteLine($_.Message)};exit 1}"
                )
                result = subprocess.run([pwsh, "-NoProfile", "-Command", command], capture_output=True, text=True)
                if result.returncode:
                    errors.append(f"invalid PowerShell {path.relative_to(ROOT)}: {result.stderr.strip()}")

    if errors:
        print("Workshop validation FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Workshop validation passed" + (" (quick)" if args.quick else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
