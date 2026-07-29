#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import time
from pathlib import Path
from typing import Any

from lib.aws_cli import AwsContext, RESULTS, read_json, require_confirmation, stack_outputs, utc_now, write_json

TERMINAL = {"Success", "Failed", "TimedOut", "Cancelled"}
AMI = re.compile(r"ami-[0-9a-f]+")


def ami_candidates(value: Any, key: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for child_key, child in value.items():
            found.extend(ami_candidates(child, f"{key}.{child_key}" if key else child_key))
    elif isinstance(value, list):
        for child in value:
            found.extend(ami_candidates(child, key))
    elif isinstance(value, str):
        found.extend((key, item) for item in AMI.findall(value))
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", required=True, choices=("APP01", "DATA01"))
    parser.add_argument("--region", required=True)
    parser.add_argument("--profile", default="default")
    parser.add_argument("--stack-name", default="kiro-ws2025-lab")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=30)
    args = parser.parse_args()
    aws = AwsContext(args.region, args.profile)
    outputs = stack_outputs(aws, args.stack_name)
    source_id = outputs["AppInstanceId" if args.server == "APP01" else "DataInstanceId"]

    compatibility = read_json(RESULTS / "compatibility/report.json")
    server_report = next(item for item in compatibility["servers"] if item["logical_name"] == args.server)
    if server_report["status"] == "blocked":
        raise SystemExit(f"{args.server} compatibility status is blocked")
    baseline = read_json(RESULTS / "tests/baseline/summary.json")
    if not baseline.get("passed"):
        raise SystemExit("Baseline tests are not passing")
    if args.server == "DATA01":
        backups = read_json(RESULTS / "backups/summary.json")
        if not backups.get("passed"):
            raise SystemExit("DATA01 native backup phase has not passed")

    parameters = {
        "IamInstanceProfile": [outputs["InstanceProfileName"]],
        "InstanceId": [source_id],
        "SubnetId": [outputs["PublicSubnetId"]],
        "TargetWindowsVersion": ["2025"],
        "KeepPreUpgradeImageBackUp": ["True"],
        "RebootInstanceBeforeTakingImage": ["False"],
    }
    require_confirmation(
        args.server, yes=args.yes,
        message=(
            f"About to start AWSEC2-CloneInstanceAndUpgradeWindows for {args.server} ({source_id}).\n"
            "Target=2025; source reboot=False; retain pre-upgrade AMI=True; expected up to ~2 hours.\n"
            "The runbook creates billable temporary EC2/EBS/AMI resources."
        ),
    )
    started = utc_now()
    response = aws.call([
        "ssm", "start-automation-execution",
        "--document-name", "AWSEC2-CloneInstanceAndUpgradeWindows",
        "--parameters", __import__("json").dumps(parameters),
        "--tags", f"Key=Project,Value=kiro-ws2025-workshop", f"Key=Role,Value={args.server}",
    ])
    execution_id = response["AutomationExecutionId"]
    path = RESULTS / f"upgrades/{args.server}.json"
    last_status = None
    execution: dict[str, Any] = {}
    while True:
        execution = aws.call(["ssm", "get-automation-execution", "--automation-execution-id", execution_id])["AutomationExecution"]
        status = execution["AutomationExecutionStatus"]
        if status != last_status:
            print(f"{utc_now()} {args.server} {execution_id}: {status}", flush=True)
            last_status = status
        evidence = {
            "server": args.server, "source_instance_id": source_id, "execution_id": execution_id,
            "started_by_script_at": started, "last_polled_at": utc_now(), "status": status,
            "parameters": parameters, "automation_execution": execution,
        }
        write_json(path, evidence)
        if status in TERMINAL:
            break
        time.sleep(args.poll_seconds)
    candidates = ami_candidates(execution.get("Outputs", {}))
    upgrade_named = [ami for key, ami in candidates if "upgrade" in key.lower() or "imageid" in key.lower()]
    upgraded_ami = upgrade_named[-1] if upgrade_named else (candidates[-1][1] if candidates else None)
    evidence["ami_candidates"] = [{"output": key, "ami_id": ami} for key, ami in candidates]
    evidence["upgraded_ami_id"] = upgraded_ami
    evidence["completed_at"] = utc_now()
    write_json(path, evidence)
    print(path)
    if status != "Success" or not upgraded_ami:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
