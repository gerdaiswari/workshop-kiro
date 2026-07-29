#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from lib.aws_cli import AwsContext, RESULTS, ROOT, parse_json_stdout, run_powershell, stack_outputs, utc_now, write_json


def aws_instance_facts(aws: AwsContext, instance_id: str) -> dict[str, Any]:
    response = aws.call(["ec2", "describe-instances", "--instance-ids", instance_id])
    instance = response["Reservations"][0]["Instances"][0]
    instance_type = instance["InstanceType"]
    type_response = aws.call(["ec2", "describe-instance-types", "--instance-types", instance_type])
    type_info = type_response["InstanceTypes"][0]
    ssm = aws.call([
        "ssm", "describe-instance-information",
        "--filters", f"Key=InstanceIds,Values={instance_id}",
    ]).get("InstanceInformationList", [])
    root = next((item for item in instance.get("BlockDeviceMappings", []) if item.get("DeviceName") in {"/dev/sda1", "/dev/xvda"}), None)
    tags = {item["Key"]: item["Value"] for item in instance.get("Tags", [])}
    return {
        "instance_id": instance_id,
        "instance_type": instance_type,
        "image_id": instance["ImageId"],
        "state": instance["State"]["Name"],
        "subnet_id": instance["SubnetId"],
        "vpc_id": instance["VpcId"],
        "security_group_ids": [group["GroupId"] for group in instance.get("SecurityGroups", [])],
        "iam_profile_arn": instance.get("IamInstanceProfile", {}).get("Arn"),
        "private_ip": instance.get("PrivateIpAddress"),
        "public_ip_present": bool(instance.get("PublicIpAddress")),
        "hypervisor": type_info.get("Hypervisor"),
        "current_generation": type_info.get("CurrentGeneration"),
        "root_volume_id": root.get("Ebs", {}).get("VolumeId") if root else None,
        "ssm_ping_status": ssm[0].get("PingStatus") if ssm else "NotManaged",
        "ssm_agent_version": ssm[0].get("AgentVersion") if ssm else None,
        "tags": tags,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect workshop AWS and Windows inventory")
    parser.add_argument("--region", required=True)
    parser.add_argument("--profile", default="default")
    parser.add_argument("--stack-name", default="kiro-ws2025-lab")
    args = parser.parse_args()
    aws = AwsContext(args.region, args.profile)
    outputs = stack_outputs(aws, args.stack_name)
    remote_script = ROOT / "scripts/remote/collect_inventory.ps1"
    servers: list[dict[str, Any]] = []
    for role, output_key in (("APP01", "AppInstanceId"), ("DATA01", "DataInstanceId")):
        instance_id = outputs[output_key]
        record: dict[str, Any] = {"logical_name": role, "instance_id": instance_id, "errors": []}
        try:
            record["aws"] = aws_instance_facts(aws, instance_id)
            invocation = run_powershell(
                aws, instance_id, remote_script,
                comment=f"Kiro workshop read-only inventory {role}", timeout_seconds=600,
            )
            record["windows"] = parse_json_stdout(invocation)
            record["ssm_command_id"] = invocation["CommandId"]
        except Exception as exc:  # Preserve partial per-server evidence.
            record["errors"].append(str(exc))
        servers.append(record)
    result = {
        "schema_version": 1,
        "collected_at": utc_now(),
        "stack_name": args.stack_name,
        "region": args.region,
        "complete": all(not server["errors"] for server in servers),
        "servers": servers,
    }
    path = RESULTS / "inventory/inventory.json"
    write_json(path, result)
    print(path)
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
