"""Source-level release gates for native pool archive builder.

Actual binary compilation/linking is covered separately by the Ubuntu CI job.
No production pool, wallet RPC or blockchain needs to run for these tests.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "services/official_pool/tools/build-native-static.sh"
MAKE = ROOT / "services/official_pool/jtgrassie/Makefile"
WORKFLOW = ROOT / ".github/workflows/pool-native-static-link-ci.yml"

ARCHIVE_TARGETS = (
    "cryptonote_basic", "cncrypto", "common", "ringct_basic", "device",
    "cryptonote_format_utils_basic", "wallet-crypto", "epee",
    "easylogging", "version", "randomx",
)


class NativeStaticGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = TOOL.read_text(encoding="utf-8")
        cls.make = MAKE.read_text(encoding="utf-8")
        cls.ci = WORKFLOW.read_text(encoding="utf-8")

    def test_library_builder_is_pinned_and_rejects_dirty_checkout(self):
        self.assertIn('actual_sha=$(git -C "$source_root" rev-parse HEAD)', self.script)
        self.assertIn('[[ "$actual_sha" == "$expected_sha" ]]', self.script)
        self.assertIn("status --porcelain --untracked-files=no", self.script)
        self.assertIn("build cache belongs to another checkout", self.script)
        self.assertIn("not a ForgeCoin consensus source checkout", self.script)

    def test_low_ram_concurrency_is_bounded(self):
        self.assertIn("FRG_BUILD_JOBS:-1", self.script)
        self.assertIn("MemTotal:", self.script)
        self.assertIn("under 4 GiB RAM", self.script)
        self.assertIn("under 8 GiB RAM", self.script)
        self.assertIn('"$jobs" -le 8', self.script)

    def test_expected_eleven_native_archive_targets(self):
        for target in ARCHIVE_TARGETS:
            with self.subTest(target=target):
                self.assertIn(target, self.script)
        self.assertIn('[[ -s "$build_root/$lib" ]]', self.script)
        self.assertIn("cmake --build", self.script)
        self.assertNotIn("make release", self.script)
        self.assertNotIn("submit_block", self.script)

    def test_arm64_does_not_inherit_x86_aes_compiler_flag(self):
        self.assertIn("ARCH := $(shell uname -m)", self.make)
        self.assertIn("OPT = -fPIC", self.make)
        self.assertIn("ifneq ($(filter x86_64 amd64,$(ARCH)),)", self.make)
        self.assertIn("OPT += -maes", self.make)
        self.assertIn("else ifneq ($(ARCH),aarch64)", self.make)
        self.assertIn("Unsupported ForgeCoin pool architecture", self.make)

    def test_ci_links_only_and_does_not_execute_pool(self):
        self.assertIn("ubuntu-22.04", self.ci)
        self.assertIn("FRG_BUILD_JOBS: '2'", self.ci)
        self.assertIn("build-native-static.sh", self.ci)
        self.assertIn("Link native C pool (DO NOT START IT)", self.ci)
        self.assertIn("readelf -h", self.ci)
        self.assertNotIn("upload-artifact", self.ci)
        self.assertNotIn("ssh ", self.ci)
        self.assertNotIn("FRG_TESTED_WALLET_PAYOUTS", self.ci)


if __name__ == "__main__":
    unittest.main()
