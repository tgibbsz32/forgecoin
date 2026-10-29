import tempfile
import unittest
from pathlib import Path
from release_readiness import audit

class ReadinessTests(unittest.TestCase):
    def test_fail_closed_missing_native_and_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app/src/main/java/org/forgecoin/p2ptest").mkdir(parents=True)
            (root / "app/src/main/AndroidManifest.xml").write_text('<application android:allowBackup="false"/>')
            (root / "app/src/main/java/org/forgecoin/p2ptest/MainActivity.java").write_text('"Create FRG wallet — unavailable"')
            checks = audit(root)
            self.assertTrue(checks["private_app_backup_disabled"])
            self.assertFalse(checks["native_frgbinary_present"])
            self.assertFalse(checks["physical_arm64_test_evidence"])
            self.assertFalse(checks["independent_security_review_signed"])
            self.assertFalse(all(checks.values()))

if __name__ == "__main__":
    unittest.main()
