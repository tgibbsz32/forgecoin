"""No-RPC regression tests for exact header-only nonce reconstruction."""
import unittest
from dataclasses import replace

from services.pool_research.nonce_candidate import build_nonce_candidate
from services.pool_research.pow_boundary import VerificationError
from services.pool_research.template_adapter import validate_template


class NonceCandidateTests(unittest.TestCase):
    def fixture(self, timestamp=b"\x01"):
        header = b"\x10\x10" + timestamp + b"\x33" * 32 + bytes(4)
        hashing = header + b"\x44" * 32 + b"\x01"
        full = header + b"\x55" * 48
        return validate_template({"result": {
            "height": 1, "difficulty": 1, "expected_reward": 1,
            "seed_hash": "ab" * 32, "blocktemplate_blob": full.hex(),
            "blockhashing_blob": hashing.hex(), "reserved_offset": len(full) - 8,
        }})

    def test_exact_four_bytes_modified(self):
        template = self.fixture()
        candidate = build_nonce_candidate(template, "01020304")
        self.assertEqual(candidate.nonce_offset, 35)
        self.assertEqual(candidate.nonce, bytes.fromhex("01020304"))
        for original, updated in (
            (template.blocktemplate_blob, candidate.full_block_blob),
            (template.blockhashing_blob, candidate.hashing_blob),
        ):
            self.assertEqual(original[:35], updated[:35])
            self.assertEqual(updated[35:39], b"\x01\x02\x03\x04")
            self.assertEqual(original[39:], updated[39:])
            self.assertEqual(len(original), len(updated))

    def test_multibyte_timestamp_changes_nonce_offset(self):
        template = self.fixture(b"\xac\x02")
        candidate = build_nonce_candidate(template, "aabbccdd")
        self.assertEqual(candidate.nonce_offset, 36)
        self.assertEqual(candidate.full_block_blob[36:40], b"\xaa\xbb\xcc\xdd")

    def test_rejects_unchanged_and_invalid_nonces(self):
        template = self.fixture()
        for nonce in ("00000000", "", "1", "f" * 9, "zzzzzzzz", 42, None):
            with self.subTest(nonce=nonce), self.assertRaises(VerificationError):
                build_nonce_candidate(template, nonce)

    def test_rejects_inconsistent_or_short_native_headers(self):
        template = self.fixture()
        for altered in (
            replace(template, blocktemplate_blob=b"\x77" + template.blocktemplate_blob[1:]),
            replace(template, blockhashing_blob=b"\x80"),
            replace(template, blockhashing_blob=b"\xff" * 12),
            replace(template, blocktemplate_blob=template.blocktemplate_blob[:38]),
        ):
            with self.subTest(altered=altered), self.assertRaises(VerificationError):
                build_nonce_candidate(altered, "01020304")

    def test_rejects_noncanonical_varint(self):
        template = self.fixture()
        mutated = b"\x90\x00" + template.blockhashing_blob[1:]
        with self.assertRaises(VerificationError):
            build_nonce_candidate(replace(template, blockhashing_blob=mutated),
                                  "01020304")


if __name__ == "__main__":
    unittest.main()
