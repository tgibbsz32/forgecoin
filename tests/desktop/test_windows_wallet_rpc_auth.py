"""Authenticated Windows FRG wallet RPC integration guardrails.

These source-level checks supplement, but do not replace, the real Windows
native wallet create/restore/restart acceptance harness.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "apps/desktop"
WORKFLOW = ROOT / ".github/workflows/desktop-frozen-mainnet-endpoints.yml"


class WalletRpcAuthenticationGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gui = (SRC / "Program.cs").read_text(encoding="utf-8")
        cls.session = (SRC / "WalletRpcSession.cs").read_text(encoding="utf-8")
        cls.transport = (SRC / "WalletRpcDigestTransport.cs").read_text(encoding="utf-8")
        cls.build = (SRC / "build.ps1").read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_wallet_rpc_never_disables_authentication(self):
        self.assertNotIn("--disable-rpc-login", self.gui)
        self.assertIn("--config-file ", self.gui)
        self.assertIn("WalletRpcSession.Create(", self.gui)
        self.assertIn("walletSession.DeleteStartupConfig()", self.gui)
        self.assertIn("if (walletSession == null)", self.gui)
        self.assertIn("walletSession.PostJson(url, payload, timeoutMs)", self.gui)
        self.assertIn("Native wallet authorization unavailable.", self.gui)
        self.assertIn("Native wallet RPC rejected the requested operation.", self.gui)

    def test_private_session_never_passes_password_in_native_argv(self):
        self.assertIn("SetAccessRuleProtection(true, false)", self.session)
        self.assertIn("WindowsIdentity.GetCurrent().User", self.session)
        self.assertIn("FileSystemRights.FullControl", self.session)
        self.assertIn("FileMode.CreateNew", self.session)
        self.assertIn("RandomNumberGenerator.Create()", self.session)
        self.assertIn("lock (requestGate)", self.session)
        self.assertIn("File.Delete(configPath)", self.session)
        self.assertIn("walletSession.Dispose();", self.gui)
        self.assertNotIn('walletSession.Password', self.gui)
        self.assertNotIn('"--rpc-login"', self.gui)

    def test_wallet_digest_challenge_bound_to_keepalive(self):
        self.assertIn('private const string Probe =', self.transport)
        self.assertIn('method\\":\\"get_version', self.transport.replace('"', '\\"'))
        self.assertIn("req.KeepAlive = true", self.transport)
        self.assertIn("using (Stream denied = response.GetResponseStream())", self.transport)
        self.assertIn('response.StatusCode == HttpStatusCode.Unauthorized', self.transport)
        self.assertIn('challenge = candidate', self.transport)
        self.assertIn('MD5', self.transport)
        self.assertIn("req.AllowAutoRedirect = false", self.transport)
        self.assertIn("req.Proxy = null", self.transport)
        self.assertIn("Native wallet RPC outcome is unverified", self.transport)
        self.assertIn('url.Host == "127.0.0.1"', self.transport)

    def test_no_wallet_output_credential_leak_into_gui_log(self):
        self.assertIn('if (prefix == "WALLET") line = "Native wallet diagnostic redacted."', self.gui)
        self.assertIn("if (choice == DialogResult.Cancel) { e.Cancel = true; return; }", self.gui)
        close = self.gui[self.gui.index("private void OnClosing("):]
        self.assertLess(close.index("if (choice == DialogResult.Cancel)"),
                        close.index("walletSession.Dispose();"))

    def test_compiled_and_disposable_windows_native_acceptance(self):
        for filename in ("WalletRpcSession.cs", "WalletRpcDigestTransport.cs"):
            self.assertIn(filename, self.build)
            self.assertIn(filename, self.workflow)
        self.assertIn("WalletRpcDigestProbe.cs", self.workflow)
        qa = (ROOT / "tests/desktop/windows/WalletRpcSessionAcceptance.cs").read_text(
            encoding="utf-8"
        )
        ps1 = (ROOT / "tests/desktop/windows/Invoke-WalletSessionAcceptance.ps1").read_text(
            encoding="utf-8"
        )
        for method in (
            '"create_wallet"', '"query_key"', '"restore_deterministic_wallet"',
            '"close_wallet"', '"open_wallet"'
        ):
            self.assertIn(method, qa)
        self.assertIn("WalletRpcSession.Create(", qa)
        self.assertIn("session.DeleteStartupConfig()", qa)
        self.assertIn("No peers, no daemon", qa.lower().replace("no peers", "No peers").replace("no daemon", "no daemon"))
        self.assertIn("windows_prelaunch_binaries_sha256", ps1)
        self.assertIn("release_authorized -ne $false", ps1)
        self.assertIn("--no-initial-sync", qa)


if __name__ == "__main__":
    unittest.main()
