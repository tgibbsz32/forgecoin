import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import stage_windows_sidecars as staging


class StagingTests(unittest.TestCase):
    def test_network_manifest_must_match_reviewed_artifacts(self):
        with tempfile.TemporaryDirectory() as root:
            manifest = Path(root) / "identity.json"
            identity = {"stage": "genesis-frozen", "genesis_hash": "a" * 64,
                        "release_authorized": False,
                        "windows_prelaunch_binaries_sha256": {
                            f"{name}.exe": digest for name, digest in staging.REVIEWED.items()}}
            manifest.write_text(json.dumps(identity), encoding="utf-8")
            staging.validate_network_identity(manifest)
            identity["windows_prelaunch_binaries_sha256"]["forged.exe"] = "b" * 64
            manifest.write_text(json.dumps(identity), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Stale sidecar audit"):
                staging.validate_network_identity(manifest)

    def test_release_or_unfrozen_identity_requires_separate_review(self):
        with tempfile.TemporaryDirectory() as root:
            manifest = Path(root) / "identity.json"
            for identity in ({"release_authorized": True}, {"release_authorized": False}):
                manifest.write_text(json.dumps(identity), encoding="utf-8")
                with self.assertRaises(ValueError):
                    staging.validate_network_identity(manifest)

    def test_pending_consensus_changes_block_old_binary_packaging(self):
        with tempfile.TemporaryDirectory() as root:
            manifest = Path(root) / "identity.json"
            manifest.write_text(json.dumps({"consensus_guard_stage": "draft-unbuilt"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "reviewed native rebuilds"):
                staging.validate_network_identity(manifest)

    def test_rejects_complete_set_before_writing(self):
        with tempfile.TemporaryDirectory() as root:
            source, dest = Path(root) / "src", Path(root) / "dest"
            source.mkdir()
            (source / "a.exe").write_bytes(b"reviewed")
            (source / "b.exe").write_bytes(b"tampered")
            with patch.object(staging, "REVIEWED", dict.fromkeys(
                    ["a", "b"], hashlib.sha256(b"reviewed").hexdigest())):
                with self.assertRaises(ValueError):
                    staging.stage(source, dest)
            self.assertFalse(dest.exists())

    def test_stages_exact_bytes_and_detects_later_replacement(self):
        with tempfile.TemporaryDirectory() as root:
            source, dest = Path(root) / "src", Path(root) / "dest"
            source.mkdir()
            (source / "a.exe").write_bytes(b"reviewed")
            with patch.object(staging, "REVIEWED", {
                    "a": hashlib.sha256(b"reviewed").hexdigest()}):
                staging.stage(source, dest)
                self.assertEqual(staging.validated(dest, True), {"a": b"reviewed"})
                (dest / f"a-{staging.TARGET}.exe").write_bytes(b"replacement")
                with self.assertRaises(ValueError):
                    staging.validated(dest, True)


if __name__ == "__main__":
    unittest.main()
