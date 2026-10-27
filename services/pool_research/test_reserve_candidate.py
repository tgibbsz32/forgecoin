"""Offline, no-RPC regression coverage for native reserve-block output."""
from dataclasses import replace
import tempfile
from pathlib import Path
import unittest

from services.pool_research.pow_boundary import VerificationError
from services.pool_research.reserve_candidate import build_reserve_candidate, check_result
from services.pool_research.template_adapter import validate_template


class ReserveCandidateTests(unittest.TestCase):
    def setUp(self):
        header = b"\x10\x10\x01" + b"3" * 32 + bytes(4)
        full = header + b"A" * 9 + b"01234567" + b"B" * 12
        hashing = header + b"C" * 32 + b"\x01"
        self.template = validate_template({"result": {
            "height": 1, "difficulty": 1, "expected_reward": 0,
            "seed_hash": "ab" * 32, "blocktemplate_blob": full.hex(),
            "blockhashing_blob": hashing.hex(), "reserved_offset": 48,
        }})
        self.replacement = b"abcdefgh"
        self.full = full[:48] + self.replacement + full[56:]
        self.hashing = header + b"D" * 32 + b"\x01"

    def message(self, *, full=None, hashing=None, offset=48):
        return ("FULL " + (self.full if full is None else full).hex() +
                "\nHASHING " + (self.hashing if hashing is None else hashing).hex() +
                "\nOFFSET " + str(offset) + "\n")

    def test_valid_exact_modification(self):
        result = check_result(self.template, self.replacement, self.message())
        self.assertEqual(result.full_block_blob, self.full)
        self.assertEqual(result.hashing_blob, self.hashing)
        self.assertEqual(result.reserve_offset, 48)

    def test_tampering_and_wrong_offsets_fail_closed(self):
        for output in (
            self.message(offset=47),
            self.message(full=self.full[:-1] + b"X"),
            self.message(hashing=self.template.blockhashing_blob),
            self.message(hashing=b"X" + self.hashing[1:]),
            self.message() + "FULL 00\n",
            "FULL garbage\nHASHING 00\nOFFSET 48\n",
            "ERROR cannot parse",
        ):
            with self.subTest(output=output[:40]), self.assertRaises(VerificationError):
                check_result(self.template, self.replacement, output)

    def test_rejects_invalid_template_and_reserve(self):
        for payload in (b"short", "not bytes", None):
            with self.assertRaises(VerificationError):
                check_result(self.template, payload, self.message())
        with self.assertRaises(VerificationError):
            check_result(replace(self.template, reserve_size=7), self.replacement, self.message())

    def test_wrong_helper_digest_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "forge-isolated-block-reconstruct.exe"
            file.write_bytes(b"not an executable")
            with self.assertRaisesRegex(VerificationError, "digest mismatch"):
                build_reserve_candidate(self.template, self.replacement, file, "0" * 64)


if __name__ == "__main__":
    unittest.main()
