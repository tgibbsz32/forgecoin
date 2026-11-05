import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("xmrig_verifier", ROOT / "tools" / "verify_xmrig_release.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class XmrigReleaseVerification(unittest.TestCase):
    def test_rejects_modified_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / verifier.ASSET
            path.write_bytes(b"not an upstream XMRig release")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                verifier.verify(path)

    def test_rejects_wrong_asset_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "xmrig-unreviewed.zip"
            path.write_bytes(b"not an upstream XMRig release")
            with self.assertRaisesRegex(ValueError, "Unexpected asset name"):
                verifier.verify(path)

    def test_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                verifier.verify(Path(tmp) / verifier.ASSET)

    def test_expected_digest_is_valid_sha256(self):
        self.assertEqual(len(bytes.fromhex(verifier.SHA256)), 32)


if __name__ == "__main__":
    unittest.main()
