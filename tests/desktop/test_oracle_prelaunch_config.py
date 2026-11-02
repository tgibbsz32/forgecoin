"""Oracle FRG selected service and firewall policy, synthetic inputs only."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import audit_oracle_prelaunch_config as audit


def snapshot():
    return {
        "launch_marker_exists": False,
        "iptables_input": (
            "-P INPUT ACCEPT\n"
            "-A INPUT -p tcp --dport 80 -j ACCEPT\n"
            "-A INPUT -p tcp --dport 443 -j ACCEPT\n"
            "-A INPUT -p tcp --dport 22 -j ACCEPT\n"
            "-A INPUT -j REJECT\n"
        ),
        "units": {
            "forgecoin.service": {
                "loaded": True, "enabled": False, "active": False,
                "unit_text": "ExecStart=/opt/legacy/forged --p2p-bind-port 19480 --rpc-bind-port 19481\n",
            },
            "forgecoin-mainnet-20261026.service": {
                "loaded": True, "enabled": False, "active": False,
                "unit_text": (
                    "[Unit]\nConditionPathExists=/etc/forgecoin/approved-mainnet-launch.json\n"
                    "[Service]\nExecStart=/opt/selected/forged "
                    "--p2p-bind-port 39480 --rpc-bind-ip 127.0.0.1 "
                    "--rpc-bind-port 39481 --zmq-rpc-bind-ip 127.0.0.1 "
                    "--zmq-rpc-bind-port 39482\n"
                ),
            },
            "forgecoin-mainnet-staging.service": {
                "loaded": True, "enabled": False, "active": False,
                "unit_text": "ExecStart=/opt/staging/forged --p2p-bind-port 39480\n",
            },
        },
    }


class OraclePrelaunchUnitAudit(unittest.TestCase):
    def test_good_selected_unit_and_retired_disabled_unit_are_not_error(self):
        result = audit.assess(snapshot())
        self.assertTrue(result["pass"])
        self.assertFalse(result["mutations_performed"])
        self.assertEqual(result["errors"], [])
        self.assertTrue(any("Disabled legacy" in x for x in result["warnings"]))

    def test_legacy_firewall_opening_is_error_even_when_daemon_inactive(self):
        x = snapshot()
        x["iptables_input"] += "-A INPUT -p tcp -m tcp --dport 19480 -j ACCEPT\n"
        result = audit.assess(x)
        self.assertFalse(result["pass"])
        self.assertIn("Oracle firewall still allows retired FRG port 19480", result["errors"])

    def test_selecting_19481_or_exposing_private_daemon_rpc_fails(self):
        x = snapshot()
        selected = x["units"]["forgecoin-mainnet-20261026.service"]
        selected["unit_text"] = selected["unit_text"].replace("--rpc-bind-port 39481", "--rpc-bind-port 19481")
        x["iptables_input"] += "-A INPUT -p tcp -m tcp --dport 39482 -j ACCEPT\n"
        result = audit.assess(x)
        self.assertIn("Selected rpc port is not 39481", result["errors"])
        self.assertIn("Oracle firewall has an explicit allow for private service port 39482", result["errors"])

    def test_fails_closed_for_enabled_or_active_services(self):
        x = snapshot()
        x["units"]["forgecoin.service"]["active"] = True
        x["units"]["forgecoin-mainnet-20261026.service"]["enabled"] = True
        result = audit.assess(x)
        self.assertTrue(any("forgecoin.service is ACTIVE" in e for e in result["errors"]))
        self.assertTrue(any("forgecoin-mainnet-20261026.service is enabled" in e for e in result["errors"]))

    def test_missing_launch_gate_or_marker_approval_fails(self):
        x = snapshot()
        x["units"]["forgecoin-mainnet-20261026.service"]["unit_text"] = (
            x["units"]["forgecoin-mainnet-20261026.service"]["unit_text"].replace(
                "ConditionPathExists=/etc/forgecoin/approved-mainnet-launch.json", ""
            )
        )
        x["launch_marker_exists"] = True
        result = audit.assess(x)
        self.assertIn("Selected mainnet unit lacks launch approval condition", result["errors"])
        self.assertIn("Launch approval marker is present or unverified", result["errors"])

    def test_missing_firewall_snapshot_does_not_report_clean(self):
        x = snapshot()
        x.pop("iptables_input")
        self.assertFalse(audit.assess(x)["pass"])

    def test_offline_cli_reports_errors_without_mutation(self):
        x = snapshot()
        x["iptables_input"] += "-A INPUT -p tcp --dport 19480 -j ACCEPT\n"
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "oracle.json"
            p.write_text(json.dumps(x), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(ROOT / "tools/audit_oracle_prelaunch_config.py"),
                 "--snapshot", str(p)],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(run.returncode, 2, run.stderr)
            result = json.loads(run.stdout)
            self.assertFalse(result["mutations_performed"])
            self.assertFalse(result["pass"])


if __name__ == "__main__":
    unittest.main()
