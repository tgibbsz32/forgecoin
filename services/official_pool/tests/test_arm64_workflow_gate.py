"""Contract of the *ephemeral* native ARM64 pool link CI.

This test does not compile a pool or infer that Oracle is safe to deploy.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WF = ROOT / ".github/workflows/pool-native-arm64-link-ci.yml"


class Arm64WorkflowGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WF.read_text(encoding="utf-8")

    def test_on_target_aarch64_runner_not_x86_cross_compile(self):
        self.assertIn("runs-on: ubuntu-24.04-arm", self.workflow)
        self.assertIn('test "$(uname -m)" = aarch64', self.workflow)
        self.assertIn("AArch64", self.workflow)

    def test_pinned_native_archives_then_pool_link(self):
        self.assertIn("build-native-static.sh", self.workflow)
        self.assertIn('"$(git rev-parse HEAD)"', self.workflow)
        self.assertIn("FRG_BUILD_JOBS: '2'", self.workflow)
        self.assertIn("build/official-pool-static/release", self.workflow)
        self.assertIn("make -C services/official_pool/jtgrassie -j 2 release", self.workflow)

    def test_no_public_miners_wallets_deployment_or_download(self):
        self.assertIn("permissions:\n  contents: read", self.workflow)
        self.assertIn("persist-credentials: false", self.workflow)
        self.assertNotIn("upload-artifact", self.workflow)
        self.assertNotIn("docker login", self.workflow)
        self.assertNotIn("ssh ", self.workflow)
        self.assertNotIn("scp ", self.workflow)
        self.assertNotIn("wallet-rpc", self.workflow)
        self.assertIn("NEVER EXECUTED", self.workflow)

    def test_no_intel_aes_flag_or_missing_runtime_dependencies(self):
        self.assertIn("ARCH=aarch64", self.workflow)
        self.assertIn("Refusing Intel-only -maes", self.workflow)
        self.assertIn("ldd \"$bin\"", self.workflow)
        self.assertIn("readelf -h", self.workflow)
        self.assertIn("not found", self.workflow)


if __name__ == "__main__":
    unittest.main()
