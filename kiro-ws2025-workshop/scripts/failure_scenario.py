#!/usr/bin/env python3
from __future__ import annotations

import argparse

from lib.aws_cli import AwsContext, RESULTS, ROOT, instance_tag_value, parse_json_stdout, read_json, require_confirmation, run_powershell, utc_now, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True, choices=("inject", "repair"))
    parser.add_argument("--region", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    aws = AwsContext(args.region, args.profile)
    state = read_json(RESULTS / "validation/state.json")
    instance_id = state["instances"]["APP01"]["instance_id"]
    role = instance_tag_value(aws, instance_id, "Role")
    project = instance_tag_value(aws, instance_id, "Project")
    if role != "VAL-APP01" or project != "kiro-ws2025-workshop":
        raise SystemExit(f"Refusing: {instance_id} tags are Role={role!r}, Project={project!r}")
    require_confirmation(
        args.action.upper(), yes=args.yes,
        message=f"{args.action} controlled KiroNext failure on validation instance {instance_id}; source APP01 is not targeted.",
    )
    script = ROOT / f"scripts/remote/{'inject' if args.action == 'inject' else 'repair'}_next_failure.ps1"
    invocation = run_powershell(aws, instance_id, script, comment=f"Kiro workshop {args.action} Next failure", timeout_seconds=300)
    evidence = parse_json_stdout(invocation)
    output = {"instance_id": instance_id, "role": role, "action": args.action, "executed_at": utc_now(), "command_id": invocation["CommandId"], "evidence": evidence}
    path = RESULTS / f"failure-scenarios/{args.action}-{utc_now().replace(':', '-')}.json"
    write_json(path, output)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
