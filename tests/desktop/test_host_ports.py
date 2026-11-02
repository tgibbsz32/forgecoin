"""Read-only Oracle listener audit parsing tests. No network connections."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import audit_host_ports


def sample(*endpoints: str) -> str:
    return "".join(f"LISTEN 0 128 {ep} 0.0.0.0:*\n" for ep in endpoints)


class PortListenerAudit(unittest.TestCase):
    def test_loopback_rpc_zmq_wallet_and_miner_are_safe(self):
        output = audit_host_ports.inspect(sample(
            "127.0.0.1:39480", "127.0.0.1:39481",
            "[::1]:39482", "127.0.0.1:39483", "[::1]:39484",
        ))
        self.assertFalse(output["fail"])
        self.assertFalse(output["alerts"])
        self.assertEqual(len(output["listeners"]), 5)

    def test_selected_p2p_public_binding_is_warning_only(self):
        output = audit_host_ports.inspect(sample("0.0.0.0:39480", "[::]:39480"))
        self.assertFalse(output["fail"])
        self.assertEqual(len(output["alerts"]), 2)
        self.assertTrue(all(e["severity"] == "warning" for e in output["alerts"]))

    def test_exposing_sensitive_services_is_an_error(self):
        for port in (39481, 39482, 39483, 39484):
            with self.subTest(port=port):
                output = audit_host_ports.inspect(sample(f"0.0.0.0:{port}"))
                self.assertTrue(output["fail"])
                self.assertEqual(output["alerts"][0]["port"], port)
                self.assertEqual(output["alerts"][0]["severity"], "error")

    def test_retired_network_listeners_are_always_reported(self):
        output = audit_host_ports.inspect(sample(
            "127.0.0.1:19480", "0.0.0.0:19481", "[::1]:19482",
        ))
        self.assertTrue(output["fail"])
        self.assertEqual([i["port"] for i in output["alerts"]], [19480, 19481, 19482])

    def test_ignores_unrelated_ports_and_invalid_lines(self):
        output = audit_host_ports.inspect(
            "SOME OTHER LOG :39481\n" + sample("127.0.0.1:443", "*:8080") +
            "LISTEN 0 128 invalid 0.0.0.0:*\n" +
            "LISTEN 0 128 [::1]:99999 0.0.0.0:*\n"
        )
        self.assertFalse(output["alerts"])
        self.assertEqual(output["listeners"], [])

    def test_cli_can_analyze_saved_fixture_without_ss_or_ssh(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ss.txt"
            path.write_text(sample("0.0.0.0:39481", "127.0.0.1:39482"), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(ROOT / "tools/audit_host_ports.py"),
                 "--ss-file", str(path), "--json"],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(completed.returncode, 2, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertTrue(result["fail"])
            self.assertEqual(result["alerts"][0]["port"], 39481)


if __name__ == "__main__":
    unittest.main()
