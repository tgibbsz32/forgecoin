#!/usr/bin/env python3
"""Read-only FRG Oracle prelaunch systemd and iptables configuration audit.

Run locally on an authorized Oracle VM. No service starts/stops, no firewall
mutations, no network connections and no output of wallet or seed material.
Pass --snapshot FILE for deterministic offline validation instead.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

SERVICES = (
    "forgecoin.service",
    "forgecoin-mainnet-20261026.service",
    "forgecoin-mainnet-staging.service",
)
SELECTED = SERVICES[1]
LEGACY = SERVICES[0]
PORT_FLAGS = {
    "p2p": ("--p2p-bind-port", "39480"),
    "rpc": ("--rpc-bind-port", "39481"),
    "zmq": ("--zmq-rpc-bind-port", "39482"),
}


def command(args: list[str]) -> str:
    cp = subprocess.run(args, capture_output=True, text=True, timeout=12, check=False)
    if cp.returncode != 0:
        raise RuntimeError(f"Read-only inspection failed: {args[0]} exit={cp.returncode}")
    return cp.stdout


def gather() -> dict:
    units = {}
    for name in SERVICES:
        show = command([
            "systemctl", "show", name, "-p", "LoadState", "-p", "UnitFileState",
            "-p", "ActiveState",
        ])
        state = dict(line.split("=", 1) for line in show.splitlines() if "=" in line)
        if state.get("LoadState") != "loaded":
            units[name] = {"loaded": False}
            continue
        units[name] = {
            "loaded": True,
            "enabled": state.get("UnitFileState") == "enabled",
            "active": state.get("ActiveState") == "active",
            "unit_text": command(["systemctl", "cat", name]),
        }
    return {
        "units": units,
        "iptables_input": command(["sudo", "-n", "iptables", "-S", "INPUT"]),
        "launch_marker_exists": Path("/etc/forgecoin/approved-mainnet-launch.json").exists(),
    }


def assess(snapshot: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    units = snapshot.get("units", {})
    if not isinstance(units, dict):
        raise ValueError("Invalid snapshot: units")

    for name in SERVICES:
        unit = units.get(name)
        if not isinstance(unit, dict) or not unit.get("loaded"):
            if name == SELECTED:
                errors.append("Selected mainnet systemd unit is missing")
            continue
        if unit.get("active"):
            errors.append(f"{name} is ACTIVE during unapproved prelaunch audit")
        if unit.get("enabled"):
            errors.append(f"{name} is enabled during unapproved prelaunch audit")
        content = str(unit.get("unit_text", ""))
        if name == SELECTED:
            for label, (flag, port) in PORT_FLAGS.items():
                if not re.search(r"(?<!\S)" + re.escape(flag) + r"\s+" + port + r"(?!\d)", content):
                    errors.append(f"Selected {label} port is not {port}")
            if not re.search(r"--rpc-bind-ip\s+127\.0\.0\.1", content):
                errors.append("Selected daemon RPC is not loopback-bound")
            if not re.search(r"--zmq-rpc-bind-ip\s+127\.0\.0\.1", content):
                errors.append("Selected ZMQ RPC is not loopback-bound")
            if "ConditionPathExists=/etc/forgecoin/approved-mainnet-launch.json" not in content:
                errors.append("Selected mainnet unit lacks launch approval condition")
            if re.search(r"(?<!\d)1948[012](?!\d)", content):
                errors.append("Selected mainnet service references retired native ports")
        elif name == LEGACY:
            if re.search(r"(?<!\d)1948[012](?!\d)", content):
                warnings.append("Disabled legacy forgecoin.service retains historical port references; never start it")
        elif name == "forgecoin-mainnet-staging.service":
            if "ConditionPathExists=" not in content:
                warnings.append("Disabled staging unit lacks launch-condition guard; manual start must remain prohibited")

    if snapshot.get("launch_marker_exists") is not False:
        errors.append("Launch approval marker is present or unverified")
    raw = snapshot.get("iptables_input")
    if not isinstance(raw, str) or not raw.strip():
        errors.append("Live iptables INPUT policy was not captured")
    else:
        for line in raw.splitlines():
            if not line.startswith("-A INPUT "):
                continue
            if "-j ACCEPT" not in line:
                continue
            for p in ("19480", "19481", "19482"):
                if re.search(r"--dport\s+" + p + r"(?!\d)", line):
                    errors.append(f"Oracle firewall still allows retired FRG port {p}")
            for p in ("39481", "39482", "39483", "39484", "4242", "4243", "19800"):
                if re.search(r"--dport\s+" + p + r"(?!\d)", line):
                    errors.append(f"Oracle firewall has an explicit allow for private service port {p}")
            if re.search(r"--dport\s+39480(?!\d)", line):
                warnings.append("Oracle firewall allows selected P2P 39480 before public launch approval")

    return {
        "classification": "READ_ONLY_PRELAUNCH_AUDIT_NOT_RELEASE_APPROVAL",
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "pass": not errors,
        "mutations_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, help="Offline JSON snapshot instead of local systemd/iptables reads")
    args = parser.parse_args()
    try:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8")) if args.snapshot else gather()
        result = assess(snapshot)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"error": str(exc), "pass": False, "mutations_performed": False}))
        return 3
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
