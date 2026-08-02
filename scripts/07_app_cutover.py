#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from typing import Any

from lib.aws_cli import AwsContext, RESULTS, instance_tag_value, read_json, require_confirmation, stack_outputs, utc_now, write_json


def health(aws: AwsContext, target_group: str) -> list[dict[str, Any]]:
    return aws.call(["elbv2", "describe-target-health", "--target-group-arn", target_group]).get("TargetHealthDescriptions", [])


def wait_healthy(aws: AwsContext, target_group: str, instance_id: str, timeout: int = 600) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        records = health(aws, target_group)
        match = next((item for item in records if item["Target"]["Id"] == instance_id), None)
        if match and match["TargetHealth"]["State"] == "healthy":
            return
        if match and match["TargetHealth"]["State"] in {"unhealthy", "unused"}:
            reason = match["TargetHealth"].get("Reason", "")
            print(f"Waiting: {instance_id} {reason}", flush=True)
        time.sleep(15)
    raise TimeoutError(f"{instance_id} did not become healthy in {target_group}")


def probe(dns: str) -> list[dict[str, Any]]:
    routes = {
        "/": "ANGULAR_OK_V1",
        "/spring/api/info": "SPRING_OK_V1",
        "/next/api/health": "NEXT_API_OK_V1",
    }
    results = []
    for route, marker in routes.items():
        try:
            with urllib.request.urlopen(f"http://{dns}{route}", timeout=20) as response:
                body = response.read().decode("utf-8", "replace")
                results.append({"route": route, "status": response.status, "marker": marker, "passed": response.status == 200 and marker in body})
        except Exception as exc:
            results.append({"route": route, "passed": False, "error": str(exc)})
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True, choices=("plan", "cutover", "rollback"))
    parser.add_argument("--region", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--stack-name", default="kiro-ws2025-lab")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    aws = AwsContext(args.region, args.profile)
    outputs = stack_outputs(aws, args.stack_name)
    state = read_json(RESULTS / "validation/state.json")
    source = outputs["AppInstanceId"]
    validation = state["instances"]["APP01"]["instance_id"]
    if instance_tag_value(aws, validation, "Role") != "VAL-APP01":
        raise SystemExit("Validation instance tag check failed")
    comparison = read_json(RESULTS / "tests/comparison.json")
    if args.action == "cutover" and not comparison.get("passed"):
        raise SystemExit("Post-upgrade comparison is not passing")
    target_groups = [outputs["AppIisTargetGroupArn"], outputs["AppNginxTargetGroupArn"]]
    before = {group: health(aws, group) for group in target_groups}
    profile_option = f" --profile {args.profile}" if args.profile else ""
    plan = {
        "action": args.action, "source_instance_id": source, "validation_instance_id": validation,
        "target_groups": target_groups, "before": before,
        "sequence": ("register validation, wait healthy, deregister source" if args.action == "cutover" else "register source, wait healthy, deregister validation"),
        "rollback_commands": {
            "windows": f"py -3 scripts\\07_app_cutover.py --action rollback --region {args.region}{profile_option} --stack-name {args.stack_name}",
            "linux_macos": f"python3 scripts/07_app_cutover.py --action rollback --region {args.region}{profile_option} --stack-name {args.stack_name}",
        },
    }
    print(json.dumps(plan, indent=2, default=str))
    if args.action == "plan":
        return 0
    expected = args.action.upper()
    require_confirmation(expected, yes=args.yes, message=f"Execute APP01 {args.action}. DATA01 is not included.")
    register_id, remove_id = (validation, source) if args.action == "cutover" else (source, validation)
    for group in target_groups:
        aws.call(["elbv2", "register-targets", "--target-group-arn", group, "--targets", f"Id={register_id}"])
        wait_healthy(aws, group, register_id)
    pre_remove_probes = probe(outputs["LoadBalancerDns"])
    if not all(item["passed"] for item in pre_remove_probes):
        raise SystemExit("Endpoint probes failed with both targets registered; source was not deregistered")
    for group in target_groups:
        aws.call(["elbv2", "deregister-targets", "--target-group-arn", group, "--targets", f"Id={remove_id}"])
    time.sleep(15)
    audit = {
        **plan, "executed_at": utc_now(), "registered_instance_id": register_id,
        "deregistered_instance_id": remove_id, "pre_remove_probes": pre_remove_probes,
        "after": {group: health(aws, group) for group in target_groups},
        "final_probes": probe(outputs["LoadBalancerDns"]),
    }
    path = RESULTS / f"cutover/{args.action}-{utc_now().replace(':', '-')}.json"
    write_json(path, audit)
    print(path)
    return 0 if all(item["passed"] for item in audit["final_probes"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
