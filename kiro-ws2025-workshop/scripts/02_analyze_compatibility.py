#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lib.aws_cli import RESULTS, utc_now, write_json


def check(check_id: str, status: str, evidence: Any, requirement: str, remediation: str = "") -> dict[str, Any]:
    return {"id": check_id, "status": status, "evidence": evidence, "requirement": requirement, "remediation": remediation}


def find_server(inventory: dict[str, Any], name: str) -> dict[str, Any]:
    return next(item for item in inventory["servers"] if item["logical_name"] == name)


def service_names(server: dict[str, Any]) -> set[str]:
    return {item["name"] for item in server.get("windows", {}).get("services", [])}


def analyze_server(server: dict[str, Any]) -> list[dict[str, Any]]:
    if server.get("errors"):
        return [check("inventory.complete", "blocker", server["errors"], "Complete measured inventory", "Resolve SSM/inventory errors")]
    aws = server["aws"]
    windows = server["windows"]
    os_info = windows["os"]
    c_drive = next((disk for disk in windows["disks"] if disk["device"] == "C:"), {})
    checks = [
        check("aws.source-os", "pass" if "2019" in os_info["caption"] else "blocker", os_info["caption"], "Windows Server 2019 source"),
        check("aws.nitro", "pass" if aws.get("hypervisor") == "nitro" else "blocker", aws.get("hypervisor"), "Nitro for 2025 target", "Move to a Nitro instance type"),
        check("aws.ssm-online", "pass" if aws.get("ssm_ping_status") == "Online" else "blocker", aws.get("ssm_ping_status"), "SSM Online"),
        check("os.powershell", "pass" if int(os_info["powershell"].split(".")[0]) >= 3 else "blocker", os_info["powershell"], "PowerShell 3 or newer"),
        check("os.tls12", "pass" if not os_info.get("tls12_client_disabled") else "blocker", os_info.get("tls12_client_disabled"), "TLS 1.2 client not disabled"),
        check("disk.free", "pass" if c_drive.get("free_gib", 0) >= 20 else "blocker", c_drive.get("free_gib"), ">=20 GiB free on C:", "Extend or clean boot volume"),
        check("roles.supported", "pass" if not windows.get("blockers") else "blocker", windows.get("blockers", []), "No excluded Windows roles"),
        check("network.internet-egress", "warning", aws.get("public_ip_present"), "Outbound internet to AWS/Microsoft", "Public IP indicates a path but run a real connectivity preflight"),
    ]
    expected = {
        "APP01": {"W3SVC", "KiroSpring", "KiroNext", "nginx"},
        "DATA01": {"Apache2.4", "MSSQL$SQLEXPRESS", "MySQL80", "postgresql-x64-15"},
    }[server["logical_name"]]
    missing = sorted(expected - service_names(server))
    checks.append(check("workloads.services", "pass" if not missing else "blocker", missing, f"Expected services: {sorted(expected)}", "Repair bootstrap or correct inventory"))
    checks.append(check("vendor.support", "unknown", sorted(expected), "Application owner/vendor confirms target OS support", "Obtain written support evidence for real workloads"))
    if server["logical_name"] == "DATA01":
        checks.append(check("data.cutover", "blocker", "point-in-time AMI", "Live data synchronization for production cutover", "Use replication or write freeze plus final native restore"))
    else:
        checks.append(check("app.cutover", "warning", "stateless synthetic lab", "Production sessions/files/dependencies assessed", "Use ALB cutover only for this synthetic lab"))
    return checks


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Compatibility report", "", f"Generated: `{report['generated_at']}`", f"Overall: **{report['overall_status']}**", ""]
    for server in report["servers"]:
        lines.extend([f"## {server['logical_name']} – {server['status']}", "", "| Check | Status | Evidence | Requirement |", "|---|---|---|---|"])
        for item in server["checks"]:
            evidence = json.dumps(item["evidence"], ensure_ascii=False).replace("|", "\\|")
            lines.append(f"| `{item['id']}` | **{item['status']}** | `{evidence}` | {item['requirement']} |")
        lines.append("")
    lines.extend([
        "## Interpretation", "",
        "`vendor.support=unknown` is intentional: the lab proves behavior, not third-party certification.",
        "`DATA01 data.cutover=blocker` blocks production cutover, not compatibility clone testing.", "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, default=RESULTS / "inventory/inventory.json")
    parser.add_argument("--output-dir", type=Path, default=RESULTS / "compatibility")
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    servers = []
    for name in ("APP01", "DATA01"):
        checks = analyze_server(find_server(inventory, name))
        technical_blockers = [item for item in checks if item["status"] == "blocker" and item["id"] != "data.cutover"]
        status = "blocked" if technical_blockers else ("conditional" if any(item["status"] in {"unknown", "warning"} for item in checks) else "eligible")
        servers.append({"logical_name": name, "status": status, "checks": checks})
    overall = "blocked" if any(item["status"] == "blocked" for item in servers) else "conditional"
    report = {"schema_version": 1, "generated_at": utc_now(), "overall_status": overall, "servers": servers}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "report.json", report)
    (args.output_dir / "report.md").write_text(render_markdown(report), encoding="utf-8")
    print(args.output_dir / "report.md")
    return 1 if overall == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
