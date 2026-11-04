"""Desktop layout and prelaunch offline-only node acceptance invariants."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
GUI = ROOT / "apps/desktop/Program.cs"
HARNESS = ROOT / "tests/desktop/windows/WinFormsGuiLayoutQa.cs"
WORKFLOW = ROOT / ".github/workflows/desktop-frozen-mainnet-endpoints.yml"

class WalletGuiSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gui = GUI.read_text(encoding="utf-8")
        cls.harness = HARNESS.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_mainnet_spending_and_mining_hard_disabled(self):
        self.assertIn("private static readonly bool NativeSpendAuthorized = false;", self.gui)
        self.assertIn("private static readonly bool NativeMiningAuthorized = false;", self.gui)
        self.assertIn("if (!NativeMiningAuthorized && !bootstrapModeBox.Checked)", self.gui)
        self.assertIn("Public FRG node bootstrap is disabled until launch", self.gui)
        self.assertIn("Private offline node QA only", self.gui)

    def test_qa_only_storage_compilation_does_not_leak_into_release(self):
        self.assertIn("#if FRG_PRIVATE_UI_QA", self.gui)
        self.assertIn('#else\n        private readonly string appRoot = Path.Combine(', self.gui)
        self.assertIn('PrivateQaPath("FRG_PRIVATE_UI_QA_ROOT")', self.gui)
        self.assertIn("frg-windows-gui-qa-", self.gui)
        # Normal production compilation must NOT define test-only root override.
        self.assertNotIn("/define:FRG_PRIVATE_UI_QA", (ROOT / "apps/desktop/build.ps1").read_text())
        self.assertIn("/define:FRG_PRIVATE_UI_QA", self.workflow)

    def test_minimum_size_wallet_ui_scrolls_and_locked_buttons_are_readable(self):
        self.assertIn('Name = "WalletPageLayout"', self.gui)
        self.assertIn("AutoScroll = true", self.gui)
        self.assertIn("AutoScrollMinSize = new Size(0, 635)", self.gui)
        self.assertIn('startMiningButton.Text = NativeMiningAuthorized ? "Start Mining" : "Launch locked"', self.gui)
        self.assertIn('startPoolButton.Text = NativeMiningAuthorized ? "Start Pool" : "Launch locked"', self.gui)
        self.assertIn("new Size(900,680)", self.harness)
        self.assertIn("new Size(1040,760)", self.harness)
        self.assertIn("ScrollControlIntoView(child)", self.harness)
        self.assertIn("walletRpc", self.harness)
        self.assertIn("poolMiner", self.harness)
        self.assertIn("Directory.GetFiles(Path.Combine(qaRoot, \"wallets\")).Length == 0", self.harness)

if __name__ == "__main__":
    unittest.main()
