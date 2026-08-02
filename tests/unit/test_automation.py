from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from lib.aws_cli import AwsContext  # noqa: E402


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SafetyHookTests(unittest.TestCase):
    def run_hook(self, command: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "hooks/block_destructive.py")],
            input=json.dumps({"tool_input": {"command": command}}),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_blocks_terminate_instances(self):
        result = self.run_hook("aws ec2 terminate-instances --instance-ids i-123")
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stderr)

    def test_allows_describe_instances(self):
        result = self.run_hook("aws ec2 describe-instances --instance-ids i-123")
        self.assertEqual(result.returncode, 0)

    def test_blocks_compound_destructive_command(self):
        result = self.run_hook("echo ok && aws cloudformation delete-stack --stack-name lab")
        self.assertEqual(result.returncode, 2)


class AwsHelperTests(unittest.TestCase):
    def test_context_adds_region_and_profile_without_shell(self):
        command = AwsContext("ap-southeast-1", "lab").command(["ec2", "describe-instances"])
        self.assertEqual(command[0], "aws")
        self.assertEqual(command[-4:], ["--region", "ap-southeast-1", "--profile", "lab"])

    def test_context_omits_profile_for_environment_credentials(self):
        command = AwsContext("us-east-1").command(["sts", "get-caller-identity"])
        self.assertEqual(command, ["aws", "sts", "get-caller-identity", "--region", "us-east-1"])


class UpgradeOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script("start_upgrade", "04_start_upgrade.py")

    def test_extracts_nested_ami_candidates_with_paths(self):
        output = {"CreateUpgradeImage.ImageId": ["ami-0123abcd"], "Other": {"backup": "ami-deadbeef"}}
        candidates = self.module.ami_candidates(output)
        self.assertIn(("CreateUpgradeImage.ImageId", "ami-0123abcd"), candidates)
        self.assertIn(("Other.backup", "ami-deadbeef"), candidates)

    def test_ignores_non_ami_values(self):
        self.assertEqual(self.module.ami_candidates({"InstanceId": "i-012345"}), [])



    def test_selects_documented_target_version_parameter(self):
        selected = self.module.select_target_version_parameter({"InstanceId", "TargetWindowsVersion"})
        self.assertEqual(selected, "TargetWindowsVersion")

    def test_accepts_runtime_target_window_version_spelling(self):
        selected = self.module.select_target_version_parameter({"InstanceId", "TargetWindowVersion"})
        self.assertEqual(selected, "TargetWindowVersion")

    def test_rejects_schema_without_target_version_parameter(self):
        with self.assertRaisesRegex(ValueError, "exposes neither"):
            self.module.select_target_version_parameter({"InstanceId", "SubnetId"})

    def test_main_pins_runtime_schema_and_uses_runtime_spelling(self):
        calls: list[list[str]] = []

        class FakeAws:
            def call(self, arguments, **_kwargs):
                calls.append(arguments)
                if arguments[:2] == ["ssm", "describe-document"]:
                    return {
                        "Document": {
                            "DocumentVersion": "46",
                            "Parameters": [
                                {"Name": "InstanceId"},
                                {"Name": "TargetWindowVersion"},
                            ],
                        }
                    }
                if arguments[:2] == ["ssm", "start-automation-execution"]:
                    return {"AutomationExecutionId": "exec-123"}
                if arguments[:2] == ["ssm", "get-automation-execution"]:
                    return {
                        "AutomationExecution": {
                            "AutomationExecutionStatus": "Success",
                            "Outputs": {"CreateUpgradeImage.ImageId": ["ami-0123abcd"]},
                        }
                    }
                self.fail(f"Unexpected AWS call: {arguments}")

        def fake_read_json(path):
            if str(path).endswith("compatibility/report.json"):
                return {"servers": [{"logical_name": "APP01", "status": "eligible"}]}
            if str(path).endswith("tests/baseline/summary.json"):
                return {"passed": True}
            self.fail(f"Unexpected evidence read: {path}")

        with tempfile.TemporaryDirectory() as directory:
            fake_aws = FakeAws()
            with (
                mock.patch.object(self.module, "AwsContext", return_value=fake_aws),
                mock.patch.object(self.module, "RESULTS", Path(directory)),
                mock.patch.object(
                    self.module,
                    "stack_outputs",
                    return_value={
                        "AppInstanceId": "i-0123456789abcdef0",
                        "InstanceProfileName": "test-profile",
                        "PublicSubnetId": "subnet-0123456789abcdef0",
                    },
                ),
                mock.patch.object(self.module, "read_json", side_effect=fake_read_json),
                mock.patch.object(self.module, "require_confirmation"),
                mock.patch.object(
                    sys,
                    "argv",
                    ["04_start_upgrade.py", "--server", "APP01", "--region", "us-east-1"],
                ),
            ):
                self.assertEqual(self.module.main(), 0)

            start_call = next(call for call in calls if call[:2] == ["ssm", "start-automation-execution"])
            self.assertEqual(start_call[start_call.index("--document-version") + 1], "46")
            parameters = json.loads(start_call[start_call.index("--parameters") + 1])
            self.assertEqual(parameters["TargetWindowVersion"], ["2025"])
            self.assertNotIn("TargetWindowsVersion", parameters)
            evidence = json.loads((Path(directory) / "upgrades/APP01.json").read_text())
            self.assertEqual(evidence["document_version"], "46")
            self.assertEqual(evidence["target_version_parameter"], "TargetWindowVersion")


class DependencyCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script("cache_dependency", "lib/cache_dependency.py")

    def test_accepts_expected_magic_size_and_sha256(self):
        content = b"MZ" + (b"binary" * 20)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "installer.exe"
            path.write_bytes(content)
            self.module.validate_file(path, len(content), b"MZ", hashlib.sha256(content).hexdigest())

    def test_rejects_html_masquerading_as_installer(self):
        content = b"<!doctype html>download page"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "installer.exe"
            path.write_bytes(content)
            with self.assertRaisesRegex(ValueError, "file magic"):
                self.module.validate_file(path, 1, b"MZ", hashlib.sha256(content).hexdigest())


if __name__ == "__main__":
    unittest.main()
