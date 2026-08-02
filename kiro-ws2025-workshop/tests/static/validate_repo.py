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
    "README.md", "docs/kiro-context-and-reuse.md", "infra/lab.yaml",
    "bootstrap/app01.ps1", "bootstrap/data01.ps1",
    "apps/app01/angular/dist/workshop-angular/index.html",
    "scripts/00_deploy.sh", "scripts/lib/cache_dependency.py", "scripts/check_kiro_prereqs.py", "scripts/01_collect_inventory.py", "scripts/02_analyze_compatibility.py",
    "scripts/03_run_tests.py", "scripts/04_start_upgrade.py", "scripts/05_launch_validation.py",
    "scripts/06_compare_results.py", "scripts/07_app_cutover.py", "scripts/08_cleanup.sh",
    ".kiro/agents/windows-upgrade.json", ".kiro/agents/windows-upgrade-windows.json",
    ".kiro/agents/upgrade-planner.json",
    ".kiro/agents/upgrade-executor.json", ".kiro/agents/upgrade-reviewer.json",
    ".kiro/skills/windows-upgrade/SKILL.md",
    "inventory/assumed-inventory.yaml",
]
VALID_HOOK_TRIGGERS = {
    "agentSpawn", "userPromptSubmit", "preToolUse", "postToolUse", "stop",
}
STEERING_INCLUSION = {
    ".kiro/steering/safety-rules.md": "always",
    ".kiro/steering/project.md": "manual",
    ".kiro/steering/aws-conventions.md": "manual",
}
TRANSFER_MODULES = [
    "modules/03-inventory-spec.md",
    "modules/04-compatibility-spec.md",
    "modules/05-hooks-and-safety.md",
    "modules/06-clone-upgrade-spec.md",
    "modules/07-validation-spec.md",
    "modules/08-cutover-rollback-spec.md",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    for relative, expected in STEERING_INCLUSION.items():
        path = ROOT / relative
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        if not re.search(rf"^---\s*\ninclusion:\s*{expected}\s*\n---", text):
            errors.append(f"{relative} must declare inclusion: {expected}")

    safety_text = (ROOT / ".kiro/steering/safety-rules.md").read_text(encoding="utf-8")
    if "APP01" in safety_text or "DATA01" in safety_text:
        errors.append("always-loaded safety steering must not contain lab server names")

    for relative in TRANSFER_MODULES:
        path = ROOT / relative
        if path.is_file() and "## Transfer to your environment" not in path.read_text(encoding="utf-8"):
            errors.append(f"workflow module missing transfer guidance: {relative}")

    for path in ROOT.rglob("*.json"):
        if "results" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")

    data_bootstrap = (ROOT / "bootstrap/data01.ps1").read_text(encoding="utf-8")
    for required_sql_fragment in (
        "SQLEXPR_x64_ENU.exe",
        "Extract SQL Server Express installation media",
        "/Q /X:",
        "Get-ChildItem $sqlExtract -Filter setup.exe",
        "SQLSVCSTARTUPTYPE=Automatic",
    ):
        if required_sql_fragment not in data_bootstrap:
            errors.append(f"DATA01 SQL bootstrap missing: {required_sql_fragment}")
    if "Get-ChildItem $sqlMedia -Filter setup.exe" in data_bootstrap:
        errors.append("DATA01 must extract SQLEXPR_x64_ENU.exe before searching for setup.exe")

    for path in ROOT.rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"invalid Python {path.relative_to(ROOT)}: {exc}")

    try:
        ET.parse(ROOT / "apps/app01/spring/pom.xml")
    except Exception as exc:
        errors.append(f"invalid Maven XML: {exc}")

    shell_files = list(ROOT.glob("scripts/*.sh"))
    for path in shell_files:
        result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
        if result.returncode:
            errors.append(f"invalid shell {path.relative_to(ROOT)}: {result.stderr.strip()}")

    for path in [ROOT / "infra/lab.yaml", ROOT / "inventory/assumed-inventory.yaml"]:
        text = path.read_text(encoding="utf-8")
        if "\t" in text:
            errors.append(f"tab character in YAML {path.relative_to(ROOT)}")

    for agent_path in sorted((ROOT / ".kiro/agents").glob("*.json")):
        agent = json.loads(agent_path.read_text(encoding="utf-8"))
        model = agent.get("model", "")
        if re.fullmatch(r"claude-(?:sonnet|haiku)-4-\d{8}", model):
            errors.append(f"obsolete model ID in {agent_path.relative_to(ROOT)}: {model}")
        hooks = agent.get("hooks", {})
        if hooks and not isinstance(hooks, dict):
            errors.append(f"agent hooks must use documented object format: {agent_path.relative_to(ROOT)}")
            continue
        for trigger, definitions in hooks.items():
            if trigger not in VALID_HOOK_TRIGGERS:
                errors.append(f"unsupported hook trigger in {agent_path.relative_to(ROOT)}: {trigger}")
            for definition in definitions:
                if not isinstance(definition, dict) or not definition.get("command"):
                    errors.append(f"hook requires a command in {agent_path.relative_to(ROOT)}: {trigger}")

    for spec in (ROOT / ".kiro/specs").iterdir():
        if spec.is_dir():
            for name in ("requirements.md", "design.md", "tasks.md"):
                if not (spec / name).is_file():
                    errors.append(f"incomplete spec {spec.name}: missing {name}")

    secret_pattern = re.compile(r"AKIA[0-9A-Z]{16}|aws_secret_access_key\s*[:=]", re.IGNORECASE)
    placeholder_pattern = re.compile(r"<from |<your |<replace|EXAMPLE", re.IGNORECASE)
    for path in ROOT.rglob("*"):
        if not path.is_file() or "results" in path.parts or path.suffix.lower() in {".png", ".jpg", ".zip"}:
            continue
        try: text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError: continue
        for line in text.splitlines():
            if secret_pattern.search(line) and not placeholder_pattern.search(line):
                errors.append(f"possible AWS secret in {path.relative_to(ROOT)}")
                break

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

        kiro_cli = shutil.which("kiro-cli")
        if kiro_cli:
            for agent_path in sorted((ROOT / ".kiro/agents").glob("*.json")):
                result = subprocess.run(
                    [kiro_cli, "agent", "validate", "--path", str(agent_path)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                if result.returncode:
                    errors.append(
                        f"Kiro agent validation failed for {agent_path.relative_to(ROOT)}: "
                        f"{(result.stdout + result.stderr).strip()}"
                    )

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
