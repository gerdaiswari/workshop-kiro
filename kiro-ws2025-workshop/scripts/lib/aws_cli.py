#!/usr/bin/env python3
"""Shared AWS CLI helpers. No boto3 dependency and no shell=True calls."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
TERMINAL_COMMAND_STATUSES = {"Success", "Cancelled", "TimedOut", "Failed", "Cancelling"}


class AwsCliError(RuntimeError):
    pass


@dataclass(frozen=True)
class AwsContext:
    region: str
    profile: str

    def command(self, service_and_args: list[str]) -> list[str]:
        return ["aws", *service_and_args, "--region", self.region, "--profile", self.profile]

    def call(self, service_and_args: list[str], *, expect_json: bool = True) -> Any:
        command = self.command(service_and_args)
        if expect_json and "--output" not in service_and_args:
            command.extend(["--output", "json"])
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        if result.returncode:
            raise AwsCliError(
                f"AWS CLI failed ({result.returncode}): {' '.join(command)}\n{result.stderr.strip()}"
            )
        if not expect_json:
            return result.stdout.strip()
        try:
            return json.loads(result.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise AwsCliError(f"Invalid JSON from {' '.join(command)}: {exc}") from exc


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stack_outputs(aws: AwsContext, stack_name: str) -> dict[str, str]:
    response = aws.call(["cloudformation", "describe-stacks", "--stack-name", stack_name])
    stacks = response.get("Stacks", [])
    if len(stacks) != 1:
        raise AwsCliError(f"Expected one stack named {stack_name}, found {len(stacks)}")
    return {item["OutputKey"]: item["OutputValue"] for item in stacks[0].get("Outputs", [])}


def require_confirmation(expected: str, *, yes: bool, message: str) -> None:
    print(message)
    if yes:
        print("Confirmation bypassed with --yes; caller owns prior approval evidence.")
        return
    actual = input(f"Type {expected} to continue: ").strip()
    if actual != expected:
        raise SystemExit("Confirmation did not match; no change made.")


def instance_tag_value(aws: AwsContext, instance_id: str, key: str) -> str | None:
    response = aws.call(["ec2", "describe-instances", "--instance-ids", instance_id])
    reservations = response.get("Reservations", [])
    instances = reservations[0].get("Instances", []) if reservations else []
    if not instances:
        return None
    tags = {tag["Key"]: tag["Value"] for tag in instances[0].get("Tags", [])}
    return tags.get(key)


def run_powershell(
    aws: AwsContext,
    instance_id: str,
    script_path: Path,
    *,
    comment: str,
    timeout_seconds: int = 1800,
) -> dict[str, Any]:
    script = script_path.read_text(encoding="utf-8")
    parameters = json.dumps({"commands": [script], "executionTimeout": [str(timeout_seconds)]})
    response = aws.call([
        "ssm", "send-command",
        "--document-name", "AWS-RunPowerShellScript",
        "--instance-ids", instance_id,
        "--comment", comment[:100],
        "--timeout-seconds", str(timeout_seconds + 60),
        "--parameters", parameters,
    ])
    command_id = response["Command"]["CommandId"]
    deadline = time.monotonic() + timeout_seconds + 120
    invocation: dict[str, Any] = {}
    while time.monotonic() < deadline:
        try:
            invocation = aws.call([
                "ssm", "get-command-invocation",
                "--command-id", command_id,
                "--instance-id", instance_id,
            ])
        except AwsCliError as exc:
            if "InvocationDoesNotExist" in str(exc):
                time.sleep(5)
                continue
            raise
        status = invocation.get("Status", "Pending")
        if status in TERMINAL_COMMAND_STATUSES:
            break
        time.sleep(10)
    else:
        raise TimeoutError(f"SSM command {command_id} exceeded timeout")
    invocation["CommandId"] = command_id
    return invocation


def parse_json_stdout(invocation: dict[str, Any]) -> Any:
    if invocation.get("Status") != "Success":
        raise AwsCliError(
            f"SSM command {invocation.get('CommandId')} status={invocation.get('Status')}: "
            f"{invocation.get('StandardErrorContent', '').strip()}"
        )
    output = invocation.get("StandardOutputContent", "").strip()
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        print(output, file=sys.stderr)
        raise AwsCliError(f"SSM output was not JSON: {exc}") from exc
