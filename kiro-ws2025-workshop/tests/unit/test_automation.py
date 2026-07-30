from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
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
