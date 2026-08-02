#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from typing import Any

from lib.aws_cli import AwsContext, RESULTS, read_json, require_confirmation, stack_outputs, utc_now, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", required=True, choices=("APP01", "DATA01"))
    parser.add_argument("--region", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--stack-name", default="kiro-ws2025-lab")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    aws = AwsContext(args.region, args.profile)
    outputs = stack_outputs(aws, args.stack_name)
    upgrade = read_json(RESULTS / f"upgrades/{args.server}.json")
    if upgrade.get("status") != "Success" or not upgrade.get("upgraded_ami_id"):
        raise SystemExit(f"Successful upgrade evidence with AMI is missing for {args.server}")
    source_id = outputs["AppInstanceId" if args.server == "APP01" else "DataInstanceId"]
    source = aws.call(["ec2", "describe-instances", "--instance-ids", source_id])["Reservations"][0]["Instances"][0]
    role = f"VAL-{args.server}"
    require_confirmation(
        role, yes=args.yes,
        message=f"Launch {role} from {upgrade['upgraded_ami_id']} as {source['InstanceType']} with public egress and no direct ingress.",
    )
    tags = [{"Key": key, "Value": value} for key, value in {
        "Name": role, "Project": "kiro-ws2025-workshop", "Environment": "validation",
        "Role": role, "SourceInstanceId": source_id, "UpgradeExecutionId": upgrade["execution_id"],
    }.items()]
    response = aws.call([
        "ec2", "run-instances",
        "--image-id", upgrade["upgraded_ami_id"],
        "--instance-type", source["InstanceType"],
        "--min-count", "1", "--max-count", "1",
        "--subnet-id", outputs["PublicSubnetId"],
        "--security-group-ids", outputs["WorkloadSecurityGroupId"],
        "--associate-public-ip-address",
        "--iam-instance-profile", f"Name={outputs['InstanceProfileName']}",
        "--metadata-options", "HttpTokens=required,HttpEndpoint=enabled,HttpPutResponseHopLimit=1",
        "--tag-specifications", __import__("json").dumps([{"ResourceType": "instance", "Tags": tags}]),
    ])
    instance_id = response["Instances"][0]["InstanceId"]
    print(f"Launched {instance_id}; waiting for EC2 status checks", flush=True)
    aws.call(["ec2", "wait", "instance-status-ok", "--instance-ids", instance_id], expect_json=False)
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        info = aws.call(["ssm", "describe-instance-information", "--filters", f"Key=InstanceIds,Values={instance_id}"]).get("InstanceInformationList", [])
        if info and info[0].get("PingStatus") == "Online":
            break
        time.sleep(15)
    else:
        raise TimeoutError(f"{instance_id} did not become SSM Online")
    state_path = RESULTS / "validation/state.json"
    state: dict[str, Any] = read_json(state_path) if state_path.exists() else {"instances": {}}
    state.update({"schema_version": 1, "updated_at": utc_now(), "region": args.region, "stack_name": args.stack_name})
    state.setdefault("instances", {})[args.server] = {
        "instance_id": instance_id, "role": role, "ami_id": upgrade["upgraded_ami_id"],
        "source_instance_id": source_id, "launched_at": utc_now(),
    }
    write_json(state_path, state)
    print(state_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
