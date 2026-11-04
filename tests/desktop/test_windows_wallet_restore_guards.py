"""Windows desktop native FRG QA release-lock integration invariants.

These are source-level checks, not proof that Windows native wallet binaries
match the frozen chain or that mainnet mining and transfers were validated.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "apps/desktop/Program.cs"
HELPER = ROOT / "apps/desktop/FrgWalletInput.cs"
BUILDER = ROOT / "apps/desktop/build.ps1"
WORKFLOW = ROOT / ".github/workflows/desktop-frozen-mainnet-endpoints.yml"


class WindowsWalletRestoreGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SRC.read_text(encoding="utf-8")
        cls.helper = HELPER.read_text(encoding="utf-8")
        cls.builder = BUILDER.read_text(encoding="utf-8")
        cls.ci = WORKFLOW.read_text(encoding="utf-8")

    def test_send_and_mining_are_not_enabled_by_configuration(self):
        self.assertIn("private static readonly bool NativeMiningAuthorized = false;", self.source)
        self.assertIn("private static readonly bool NativeSpendAuthorized = false;", self.source)
        for method, gate in (
            ("StartMining", "if (!NativeMiningAuthorized)"),
            ("StartPoolMining", "if (!NativeMiningAuthorized)"),
            ("SendFunds", "if (!NativeSpendAuthorized)"),
        ):
            start = self.source.index("private void " + method + "(")
            end = self.source.find("\n        private ", start + 13)
            if end == -1:
                end = len(self.source)
            self.assertIn(gate, self.source[start:end], method)
        self.assertIn("sendButton.Enabled = NativeSpendAuthorized;", self.source)
        self.assertIn("startMiningButton.Enabled = NativeMiningAuthorized;", self.source)
        self.assertIn("startPoolButton.Enabled = NativeMiningAuthorized;", self.source)

    def test_restore_is_private_seed_only_no_filename_overwrite(self):
        self.assertIn('Restore 25 words', self.source)
        self.assertIn('"restore_deterministic_wallet"', self.source)
        self.assertIn('"restore_height", 0', self.source)
        self.assertIn("EnsureWalletService(); // refuse missing native RPC before requesting a seed", self.source)
        self.assertIn("FrgWalletInput.NormalizeEnglishMnemonic(seedInput.Text)", self.source)
        self.assertIn("WalletFileAlreadyExists(name)", self.source)
        self.assertIn("seedInput.Clear();", self.source)
        self.assertIn('p["seed"] = String.Empty', self.source)
        self.assertIn("private QA", self.source.lower())
        self.assertNotIn("AppendLog(prefix, seed", self.source)

    def test_native_amount_parsing_never_rounds_payment(self):
        self.assertIn("FrgWalletInput.ParseAmountAtoms(sendAmountBox.Text.Trim())", self.source)
        self.assertIn("atoms != Decimal.Truncate(atoms)", self.helper)
        self.assertIn("NumberStyles.AllowDecimalPoint", self.helper)
        self.assertNotIn("decimal.Round(amount * AtomicUnits", self.source)
        self.assertIn('"validate_address"', self.source)
        self.assertIn('"any_net_type", false', self.source)
        self.assertIn("FrgWalletInput.IsTransactionId(tx)", self.source)
        self.assertIn('"get_tx_key", false', self.source)

    def test_ambiguous_transfer_is_never_retried(self):
        self.assertIn("submissionAttempted = true;", self.source)
        self.assertIn("Do NOT", self.source)
        self.assertIn("retry automatically", self.source)
        self.assertIn("Interlocked.CompareExchange(ref transferInFlight, 1, 0)", self.source)

    def test_native_helper_is_present_in_both_compilation_paths(self):
        self.assertIn('"$ProjectRoot\\FrgWalletInput.cs"', self.builder)
        self.assertIn("$frgWallet = Join-Path $src 'FrgWalletInput.cs'", self.ci)
        self.assertIn("$program $frgWallet $wallet $vault", self.ci)
        self.assertIn("FrgWalletInputTests.cs", self.ci)
        self.assertIn("RestoreWallet(object sender", self.source)


if __name__ == "__main__":
    unittest.main()
