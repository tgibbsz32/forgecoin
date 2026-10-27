"""No-network tests for binding a miner's submitted nonce to a native block."""
from dataclasses import replace
import unittest

from services.pool_research.isolated_miner_candidate import IsolatedMinerJob
from services.pool_research.pow_boundary import VerificationError
from services.pool_research.share_preflight import SharePreflightError
from services.pool_research.reserved_candidate import _miner_tx_root
from services.pool_research.template_adapter import validate_template


def fixture():
    header = b"\x10\x13\x80\x80\x80\x80\x01" + b"\x33"*32 + bytes(4)
    extra = b"\x01" + b"\x44"*32 + b"\x02\x08" + bytes(8)
    prefix = (b"\x02\x3d\x01\xff\x01\x01\x01\x03"
              + b"\x55"*33 + bytes((len(extra),)) + extra)
    full = header + prefix + b"\x00\x00"
    root = _miner_tx_root(full, len(header), len(full)-2)
    return validate_template({"result": {
        "height": 1, "difficulty": 1, "expected_reward": 1,
        "seed_hash": "ab"*32, "blocktemplate_blob": full.hex(),
        "blockhashing_blob": (header+root+b"\x01").hex(),
        "reserved_offset": len(full)-10,
    }})


class IsolatedMinerCandidateTests(unittest.TestCase):
    def test_valid_submission_reconstructs_full_block(self):
        job = IsolatedMinerJob(fixture(), "1122334455667788")
        self.assertEqual(job.nonce_offset, 39)
        captured = []
        def native(seed, blob):
            captured.append((seed, blob))
            return b"\x42"*32
        candidate = job.verify_submission(
            job.job_id, "01020304", "42"*32, native)
        self.assertEqual(candidate.full_block_blob[39:43], bytes.fromhex("01020304"))
        self.assertEqual(candidate.full_block_blob[job.original.reserved_offset:
                         job.original.reserved_offset+8], bytes.fromhex("1122334455667788"))
        self.assertEqual(captured[0][1], candidate.hashing_blob)
        self.assertEqual(candidate.digest_hex, "42"*32)
        self.assertEqual(len(captured), 1)

    def test_digest_mismatch_fails_closed(self):
        job = IsolatedMinerJob(fixture(), "1122334455667788")
        with self.assertRaisesRegex(VerificationError, "digest differs"):
            job.verify_submission(job.job_id, "01020304", "00"*32,
                                  lambda seed, blob: b"\x42"*32)
        # A failed claimed-hash submission still burns its job nonce.
        with self.assertRaisesRegex(SharePreflightError, "duplicate nonce"):
            job.verify_submission(job.job_id, "01020304", "42"*32,
                                  lambda seed, blob: b"\x42"*32)

    def test_wrong_job_and_invalid_result_rejected_before_hash(self):
        job = IsolatedMinerJob(fixture(), "1122334455667788")
        def never(seed, blob):
            raise AssertionError("should not hash")
        for ident, result in (("f"*32, "42"*32), (job.job_id, "not-a-hash")):
            with self.assertRaises(VerificationError):
                job.verify_submission(ident, "01020304", result, never)

    def test_nonisolated_templates_rejected(self):
        sample = fixture()
        for bad in (replace(sample, height=2), replace(sample, difficulty=2)):
            with self.assertRaises(VerificationError):
                IsolatedMinerJob(bad, "1122334455667788")


if __name__ == "__main__":
    unittest.main()
