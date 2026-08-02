#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from lib.aws_cli import AwsContext, AwsCliError, RESULTS, read_json, require_confirmation, utc_now, write_json


def recorded_resources() -> dict[str, Any]:
    deployment = read_json(RESULTS / "deployment/state.json")
    validation_path = RESULTS / "validation/state.json"
    validation = read_json(validation_path) if validation_path.exists() else {"instances": {}}
    instances = [item["instance_id"] for item in validation.get("instances", {}).values()]
    amis: set[str] = set()
    for server in ("APP01", "DATA01"):
        path = RESULTS / f"upgrades/{server}.json"
        if path.exists():
            evidence = read_json(path)
            for item in evidence.get("ami_candidates", []):
                amis.add(item["ami_id"])
            if evidence.get("upgraded_ami_id"):
                amis.add(evidence["upgraded_ami_id"])
    return {"deployment": deployment, "validation_instances": sorted(instances), "amis": sorted(amis)}


def image_and_snapshots(aws: AwsContext, ami_id: str) -> dict[str, Any]:
    response = aws.call(["ec2", "describe-images", "--owners", "self", "--image-ids", ami_id])
    images = response.get("Images", [])
    if not images:
        return {"ami_id": ami_id, "owned": False, "snapshots": []}
    snapshots = sorted({mapping.get("Ebs", {}).get("SnapshotId") for mapping in images[0].get("BlockDeviceMappings", []) if mapping.get("Ebs", {}).get("SnapshotId")})
    return {"ami_id": ami_id, "owned": True, "name": images[0].get("Name"), "snapshots": snapshots}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--region", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--stack-name", default="kiro-ws2025-lab")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    aws = AwsContext(args.region, args.profile)
    resources = recorded_resources()
    if resources["deployment"]["stack_name"] != args.stack_name or resources["deployment"]["region"] != args.region:
        raise SystemExit("Recorded deployment state does not match requested stack/region")
    images = []
    for ami_id in resources["amis"]:
        try: images.append(image_and_snapshots(aws, ami_id))
        except AwsCliError as exc: images.append({"ami_id": ami_id, "error": str(exc)})
    plan = {
        "generated_at": utc_now(), "stack_name": args.stack_name, "region": args.region,
        "artifact_bucket": resources["deployment"]["artifact_bucket"],
        "validation_instances": resources["validation_instances"], "images": images,
    }
    write_json(RESULTS / "cleanup-plan.json", plan)
    print(json.dumps(plan, indent=2))
    if args.plan:
        return 0
    require_confirmation(args.stack_name, yes=args.yes, message="Destructive cleanup of ONLY the recorded workshop resources above.")
    for instance_id in resources["validation_instances"]:
        role = aws.call(["ec2", "describe-instances", "--instance-ids", instance_id])["Reservations"][0]["Instances"][0].get("Tags", [])
        tags = {item["Key"]: item["Value"] for item in role}
        if tags.get("Project") != "kiro-ws2025-workshop" or not tags.get("Role", "").startswith("VAL-"):
            raise SystemExit(f"Refusing to terminate {instance_id}: tag safeguard failed")
        aws.call(["ec2", "terminate-instances", "--instance-ids", instance_id])
    for image in images:
        if not image.get("owned"):
            continue
        aws.call(["ec2", "deregister-image", "--image-id", image["ami_id"]])
        for snapshot_id in image["snapshots"]:
            aws.call(["ec2", "delete-snapshot", "--snapshot-id", snapshot_id])
    aws.call(["cloudformation", "delete-stack", "--stack-name", args.stack_name], expect_json=False)
    aws.call(["cloudformation", "wait", "stack-delete-complete", "--stack-name", args.stack_name], expect_json=False)
    bucket = resources["deployment"]["artifact_bucket"]
    subprocess.run(aws.command(["s3", "rm", f"s3://{bucket}", "--recursive"]), check=True)
    aws.call(["s3api", "delete-bucket", "--bucket", bucket], expect_json=False)
    write_json(RESULTS / "cleanup-result.json", {"completed_at": utc_now(), "plan": plan, "status": "complete"})
    print("Cleanup complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
