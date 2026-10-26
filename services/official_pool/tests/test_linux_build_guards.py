"""Static regression guards for the isolated, non-linking Linux build gate.

These tests assert *source safeguards* only. The GitHub Actions Linux job
actually compiles the nine objects; a full FRG daemon/pool link is out of scope.
"""
from pathlib import Path
import unittest

POOL_DIR = Path(__file__).resolve().parents[1] / "jtgrassie"
MAKEFILE = POOL_DIR / "Makefile"


class LinuxBuildGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.make = MAKEFILE.read_text(encoding="utf-8")

    def test_compile_check_never_links_or_installs(self):
        self.assertIn("compile-check: preflight dirs $(OBJECTS) $(COBJECTS) $(SOBJECTS) $(HTMLOBJECTS)", self.make)
        self.assertNotIn("compile-check: $(TARGET)", self.make)
        self.assertIn('PASS: compiled all ForgeCoin pool C/C++/web UI objects (NOT LINKED)', self.make)
        self.assertIn("$(OBJECTS) $(COBJECTS) $(SOBJECTS) $(HTMLOBJECTS): | dirs", self.make)

    def test_link_preflight_requires_pinned_static_archives(self):
        self.assertIn("link-preflight:", self.make)
        self.assertIn("for lib in $(MONERO_LIBS)", self.make)
        self.assertIn('if [ ! -f "$$lib" ]', self.make)
        self.assertIn("build the reviewed ForgeCoin native static archives", self.make)
        self.assertIn("$(HTMLOBJECTS) link-preflight", self.make)

    def test_frg_root_explicit_and_payout_guard_preserved(self):
        self.assertIn("Set FORGECOIN_ROOT to an explicitly reviewed ForgeCoin source checkout", self.make)
        self.assertIn("MONERO_ROOT := $(FORGECOIN_ROOT)", self.make)
        pool = (POOL_DIR / "src" / "pool.c").read_text(encoding="utf-8")
        self.assertIn("#ifndef FRG_TESTED_WALLET_PAYOUTS", pool)
        self.assertIn("#ifndef FRG_REVIEWED_PUBLIC_POOL", pool)


if __name__ == "__main__":
    unittest.main()
