import tempfile
import os
import subprocess
import unittest
from pathlib import Path
from services.pool_research.isolated_daemon import offline_daemon_args

class IsolatedDaemonTests(unittest.TestCase):
    def test_offline_loopback_only(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/"forged.exe";exe.write_bytes(b"test fixture")
            argv=offline_daemon_args(exe,Path(d)/"fresh")
            self.assertIn("--offline",argv)
            self.assertIn("--no-igd",argv)
            self.assertIn("--disable-dns-checkpoints",argv)
            self.assertEqual(argv[argv.index("--check-updates")+1],"disabled")
            for flag in ("--rpc-bind-ip","--p2p-bind-ip","--zmq-rpc-bind-ip"):
                self.assertEqual(argv[argv.index(flag)+1],"127.0.0.1")
    def test_reject_existing_data_and_duplicate_ports(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/"forged.exe";exe.write_bytes(b"fixture")
            data=Path(d)/"data";data.mkdir();(data/"existing").write_text("do not touch")
            with self.assertRaises(ValueError):offline_daemon_args(exe,data)
            with self.assertRaises(ValueError):offline_daemon_args(exe,Path(d)/"fresh",49581,49581,49582)
    def test_candidate_binary_supported_flags_when_configured(self):
        binary=os.environ.get("FORGECOIN_DAEMON_BIN")
        if not binary:
            self.skipTest("Set FORGECOIN_DAEMON_BIN to check real executable help")
        with tempfile.TemporaryDirectory() as d:
            argv=offline_daemon_args(binary,Path(d)/"fresh")
        help_text=subprocess.run([binary,"--help"],capture_output=True,text=True,timeout=20,errors="replace").stdout
        for flag in argv[1:]:
            if flag.startswith("--"):
                self.assertIn(flag,help_text)
        for flag in ("--offline","--no-igd"):
            self.assertIn(flag,help_text)
if __name__=="__main__":unittest.main()
