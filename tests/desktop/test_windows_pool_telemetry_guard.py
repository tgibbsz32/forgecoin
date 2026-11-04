"""Desktop pool miner telemetry guards against native XMRig ABI mismatch.

The ordinary desktop and private prelaunch packages remain launch locked;
offline QA is not evidence of real Stratum reward or payout settlement.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
GUI = ROOT / "apps" / "desktop" / "Program.cs"
STATUS = ROOT / "apps" / "desktop" / "XmrigPoolStatus.cs"
TESTS = ROOT / "tests" / "desktop" / "windows" / "XmrigPoolStatusTests.cs"


class WindowsPoolTelemetrySafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gui = GUI.read_text(encoding="utf-8")
        cls.status = STATUS.read_text(encoding="utf-8")
        cls.tests = TESTS.read_text(encoding="utf-8")

    def test_id_fits_real_xmrig_api_limit_and_has_process_identity(self):
        self.assertIn("byte[] monitorId = new byte[12];", self.gui)
        self.assertIn('"--api-id=" + poolApiId', self.gui)
        self.assertIn("expectedApiId.Length > 31", self.status)
        self.assertIn("actualId.Length > 31", self.status)
        self.assertIn("!String.Equals(actualId, expectedApiId", self.status)
        self.assertIn("poolApiId != result.ApiId", self.gui)
        self.assertIn("poolApiId = null;", self.gui)
        self.assertIn("new string('a', 32)", self.tests)
        self.assertIn("new string('b', 24)", self.tests)

    def test_pool_read_is_bounded_loopback_only(self):
        self.assertIn('endpoint.Host != "127.0.0.1"', self.gui)
        self.assertIn('endpoint.Port != 39483', self.gui)
        self.assertIn('endpoint.AbsolutePath != "/2/summary"', self.gui)
        self.assertIn("http.Proxy = null;", self.gui)
        self.assertIn("http.AllowAutoRedirect = false;", self.gui)
        self.assertIn("output.Length + size > 512 * 1024", self.gui)

    def test_public_spending_mining_remain_locked(self):
        self.assertIn("private static readonly bool NativeMiningAuthorized = false;", self.gui)
        self.assertIn("private static readonly bool NativeSpendAuthorized = false;", self.gui)
        self.assertIn('if (!NativeMiningAuthorized)\n                    throw new InvalidOperationException("Public pool mining remains disabled', self.gui)

    def test_connected_does_not_mean_hashing_or_shares(self):
        self.assertIn('phase = "Connecting";', self.status)
        self.assertIn('phase = "Connected";', self.status)
        self.assertIn('phase = "Hashing";', self.status)
        self.assertIn('phase = "Other pool";', self.status)
        self.assertIn('phase = "Paused";', self.status)
        self.assertIn("good, total - good", self.status)

if __name__ == "__main__":
    unittest.main()
