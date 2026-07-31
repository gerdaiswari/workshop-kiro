#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from lib.aws_cli import AwsContext, RESULTS, ROOT, parse_json_stdout, read_json, run_powershell, stack_outputs, utc_now, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=("baseline", "post", "backup-data"))
    parser.add_argument("--region", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--stack-name", default="kiro-ws2025-lab")
    args = parser.parse_args()
    aws = AwsContext(args.region, args.profile)
    outputs = stack_outputs(aws, args.stack_name)

    if args.phase == "backup-data":
        targets = [("DATA01", outputs["DataInstanceId"], ROOT / "scripts/remote/backup_data01.ps1")]
        output_dir = RESULTS / "backups"
    elif args.phase == "baseline":
        targets = [
            ("APP01", outputs["AppInstanceId"], ROOT / "scripts/remote/validate_app01.ps1"),
            ("DATA01", outputs["DataInstanceId"], ROOT / "scripts/remote/validate_data01.ps1"),
        ]
        output_dir = RESULTS / "tests/baseline"
    else:
        state = read_json(RESULTS / "validation/state.json")
        targets = [
            ("APP01", state["instances"]["APP01"]["instance_id"], ROOT / "scripts/remote/validate_app01.ps1"),
            ("DATA01", state["instances"]["DATA01"]["instance_id"], ROOT / "scripts/remote/validate_data01.ps1"),
        ]
        output_dir = RESULTS / "tests/post"

    output_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {"phase": args.phase, "tested_at": utc_now(), "servers": {}, "passed": True}
    for role, instance_id, script in targets:
        try:
            invocation = run_powershell(aws, instance_id, script, comment=f"Kiro workshop {args.phase} {role}", timeout_seconds=1800)
            evidence = parse_json_stdout(invocation)
            record = {"instance_id": instance_id, "command_id": invocation["CommandId"], "evidence": evidence}
            write_json(output_dir / f"{role}.json", record)
            server_pass = bool(evidence.get("passed"))
            summary["servers"][role] = {"instance_id": instance_id, "passed": server_pass, "file": str(output_dir / f"{role}.json")}
            summary["passed"] = summary["passed"] and server_pass
        except Exception as exc:
            summary["servers"][role] = {"instance_id": instance_id, "passed": False, "error": str(exc)}
            summary["passed"] = False
    write_json(output_dir / "summary.json", summary)
    print(output_dir / "summary.json")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
