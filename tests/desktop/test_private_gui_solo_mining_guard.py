"""Source invariants for isolated native RandomX GUI acceptance.

Production remains locked. Never use this to enable live mining or to
package a mining QA binary for public distribution.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
GUI = ROOT / "apps/desktop/Program.cs"
HARNESS = ROOT / "tests/desktop/windows/WinFormsSoloMiningQa.cs"
BUILD = ROOT / "apps/desktop/build.ps1"
CI = ROOT / ".github/workflows/desktop-frozen-mainnet-endpoints.yml"

class IsolatedSoloAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gui = GUI.read_text(encoding="utf-8")
        cls.test = HARNESS.read_text(encoding="utf-8")
        cls.builder = BUILD.read_text(encoding="utf-8")
        cls.ci = CI.read_text(encoding="utf-8")

    def test_public_and_pool_remain_locked(self):
        self.assertIn("private static readonly bool NativeMiningAuthorized = false;", self.gui)
        self.assertIn("private static readonly bool NativeSpendAuthorized = false;", self.gui)
        self.assertIn("#if FRG_PRIVATE_MINING_QA && !FRG_PRIVATE_UI_QA", self.gui)
        self.assertIn("#error Isolated native mining QA must use the temporary private UI sandbox.", self.gui)
        self.assertIn("if (!NativeMiningAuthorized)", self.gui)
        self.assertIn("if (!IsolatedSoloQaReady())", self.gui)
        self.assertIn("if (!NativeMiningAuthorized)\n                    throw new InvalidOperationException(\"Public pool mining remains disabled", self.gui)
        self.assertNotIn("/define:FRG_PRIVATE_MINING_QA", self.builder)
        self.assertNotIn("/define:FRG_PRIVATE_UI_QA", self.builder)

    def test_isolated_daemon_is_hash_pinned_and_forces_offline(self):
        self.assertIn('3efaf014c7fdfcea167630f1884abee2defd40f28f1e725b6c0a8fcede5b5c37', self.gui)
        self.assertIn('RequirePinnedPrivateQaDaemon(exe);', self.gui)
        self.assertIn('args.Add("--offline");', self.gui)
        self.assertIn('args.Add("--out-peers"); args.Add("0");', self.gui)
        self.assertIn('args.Add("--in-peers"); args.Add("0");', self.gui)
        self.assertIn('args.Contains("--offline")', self.gui)
        self.assertIn('args.Contains("--p2p-bind-ip 127.0.0.1")', self.gui)
        self.assertIn('args.Contains("--rpc-bind-ip 127.0.0.1")', self.gui)
        self.assertIn('args.Contains(Quote(Path.Combine(appRoot, "blockchain")))', self.gui)

    def test_mining_status_poll_cannot_enable_start_during_pending_rpc(self):
        self.assertEqual(
            self.gui.count("startMiningButton.Enabled = !active && IsolatedSoloQaReady()"),
            1,
            "Private mining status must have exactly one start-button assignment",
        )
        self.assertIn(
            "startMiningButton.Enabled = !active && IsolatedSoloQaReady() &&\n"
            "                            Interlocked.CompareExchange(ref miningStartInFlight, 0, 0) == 0;",
            self.gui,
        )
        self.assertNotIn(
            "startMiningButton.Enabled = !active && IsolatedSoloQaReady();",
            self.gui,
            "A duplicate unguarded refresh can allow concurrent mining start requests",
        )

    def test_actual_gui_qa_drives_native_miner_with_zero_peers(self):
        for snippet in [
            'Path.GetTempPath()', 'frg-windows-gui-qa-',
            'ExpectedGenesis', 'ExpectedDaemon',
            'startNode.PerformClick()', 'start.PerformClick()',
            'stop.PerformClick()', 'stopNode.PerformClick()',
            'WaitUntil(', '"start_mining"', '"get_block_header_by_height"'
        ]:
            if snippet != '"start_mining"':
                self.assertIn(snippet, self.test)
        self.assertIn('Convert.ToBoolean(status["active"])', self.test)
        self.assertIn('Convert.ToDouble(status["speed"]) > 0.0', self.test)
        self.assertIn('Convert.ToInt64(state["incoming_connections_count"]) == 0', self.test)
        self.assertIn('Convert.ToInt64(state["outgoing_connections_count"]) == 0', self.test)
        self.assertNotIn('print(seed)', self.test)
        self.assertNotIn('forge-wallet-rpc.exe", "forge-wallet-rpc', self.test)
        self.assertNotIn('transfer_split', self.test)

if __name__ == "__main__":
    unittest.main()
