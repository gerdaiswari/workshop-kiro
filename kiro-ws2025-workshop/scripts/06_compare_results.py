#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.aws_cli import RESULTS, utc_now, write_json


def load_checks(path: Path) -> dict[str, dict[str, Any]]:
    record = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in record["evidence"]["checks"]}


def main() -> int:
    servers: dict[str, Any] = {}
    overall = True
    for name in ("APP01", "DATA01"):
        before = load_checks(RESULTS / f"tests/baseline/{name}.json")
        after = load_checks(RESULTS / f"tests/post/{name}.json")
        ids = sorted(set(before) | set(after))
        differences = []
        passed = True
        for check_id in ids:
            old, new = before.get(check_id), after.get(check_id)
            mandatory = bool((new or old or {}).get("mandatory", True))
            ok = bool(new and new.get("passed")) if mandatory else True
            if not ok:
                passed = False
            differences.append({
                "id": check_id, "mandatory": mandatory, "passed_after": bool(new and new.get("passed")),
                "baseline_value": old.get("value") if old else None,
                "post_value": new.get("value") if new else None,
                "changed": bool(old and new and old.get("value") != new.get("value")),
                "missing_before": old is None, "missing_after": new is None,
            })
        servers[name] = {"passed": passed, "checks": differences}
        overall = overall and passed
    report = {"schema_version": 1, "compared_at": utc_now(), "passed": overall, "servers": servers}
    write_json(RESULTS / "tests/comparison.json", report)
    lines = ["# Baseline/post comparison", "", f"Overall: **{'PASS' if overall else 'FAIL'}**", ""]
    for name, server in servers.items():
        lines.extend([f"## {name} – {'PASS' if server['passed'] else 'FAIL'}", "", "| Check | Mandatory | Post pass | Baseline | Post |", "|---|---:|---:|---|---|"])
        for item in server["checks"]:
            lines.append(f"| `{item['id']}` | {item['mandatory']} | {item['passed_after']} | `{item['baseline_value']}` | `{item['post_value']}` |")
        lines.append("")
    (RESULTS / "tests/comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print(RESULTS / "tests/comparison.md")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
