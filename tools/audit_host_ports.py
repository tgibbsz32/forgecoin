#!/usr/bin/env python3
"""Read-only listener audit for ForgeCoin's frozen 20261026 host port contract.

Run this on an authorized Oracle/node host, not against an external IP.
Uses only 'ss -H -ltn'. Does not alter firewalls or process configuration.
Not a check for RPC authentication, DNS, service identity, or launch approval.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SENSITIVE = {
    39481: "daemon RPC",
    39482: "ZMQ RPC",
    39483: "XMRig local statistics",
    39484: "Windows wallet RPC",
}
RETIRED = {19480: "retired P2P", 19481: "retired daemon RPC", 19482: "retired ZMQ RPC"}
P2P = 39480
ALL = set(SENSITIVE) | set(RETIRED) | {P2P}
LOOPBACK = {"127.0.0.1", "::1", "[::1]", "localhost"}


def parse_endpoint(value: str) -> tuple[str, int] | None:
    """Read an ss Local Address:Port without interpreting unrelated fields."""
    match = re.fullmatch(r"(.+):(\d{1,5})", value)
    if not match:
        return None
    host = match.group(1).strip("[]").split("%", 1)[0]
    port = int(match.group(2))
    if not (0 < port < 65536):
        return None
    return host, port


def inspect(text: str) -> dict:
    listeners = []
    alerts = []
    seen = set()
    for line in text.splitlines():
        fields = line.split()
        # Standard 'ss -H -ltn': LISTEN Recv-Q Send-Q Local Peer.
        if len(fields) < 5 or fields[0] != "LISTEN":
            continue
        parsed = parse_endpoint(fields[3])
        if not parsed:
            continue
        host, port = parsed
        if port not in ALL or (host, port) in seen:
            continue
        seen.add((host, port))
        local = host in LOOPBACK
        kind = RETIRED.get(port) or SENSITIVE.get(port) or "P2P"
        listeners.append({"port": port, "bind": host, "service": kind, "loopback": local})
        if port in RETIRED:
            alerts.append({
                "severity": "error", "port": port,
                "reason": "Retired FRG listener; identify/isolate legacy service before deployment",
            })
        elif port in SENSITIVE and not local:
            alerts.append({
                "severity": "error", "port": port,
                "reason": "Sensitive FRG control/telemetry listener not bound to loopback; review exposure",
            })
        elif port == P2P and not local:
            alerts.append({
                "severity": "warning", "port": port,
                "reason": "P2P externally bound; do not allow public mining before release approval",
            })
    listeners.sort(key=lambda x: (x["port"], x["bind"]))
    alerts.sort(key=lambda x: (x["port"], x["severity"]))
    return {
        "scope": "local LISTEN sockets only (not process identity, firewall, production readiness)",
        "selected_native_ports": {"p2p": 39480, "daemon_rpc": 39481, "zmq_rpc": 39482},
        "listeners": listeners,
        "alerts": alerts,
        "fail": any(x["severity"] == "error" for x in alerts),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ss-file", type=Path, help="Read saved ss -H -ltn output; do not query the host")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable findings")
    args = parser.parse_args()
    if args.ss_file:
        data = args.ss_file.read_text(encoding="utf-8")
    else:
        try:
            completed = subprocess.run(
                ["ss", "-H", "-ltn"], capture_output=True, text=True, timeout=10, check=True
            )
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"ERROR: Could not inspect local TCP listeners: {exc}", file=sys.stderr)
            return 3
        data = completed.stdout
    result = inspect(data)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("FRG host port audit (read only, localhost socket listing)")
        for item in result["listeners"]:
            print(f"  {item['service']}: {item['bind']}:{item['port']}")
        for alert in result["alerts"]:
            print(f"  {alert['severity'].upper()} {alert['port']}: {alert['reason']}")
        if not result["alerts"]:
            print("No selected/retired port exposure alerts in observed listeners.")
        print("NOTE: This does not certify Oracle settings or public launch readiness.")
    return 2 if result["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
