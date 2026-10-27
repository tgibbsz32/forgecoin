"""Regression checks for restricted single-transaction coinbase reconstruction."""
import unittest
from dataclasses import replace

from services.pool_research.pow_boundary import VerificationError
from services.pool_research.reserved_candidate import (
    build_reserved_candidate, keccak_256, _miner_tx_root,
)
from services.pool_research.template_adapter import validate_template


def fixture():
    header = b"\x10\x13\x01" + b"\x33"*32 + bytes(4)
    extra = b"\x01" + b"\x44"*32 + b"\x02\x08" + bytes(8)
    prefix = (b"\x02\x3d\x01\xff\x01\x01\x01\x03"
              + b"\x55"*33 + bytes((len(extra),)) + extra)
    full = header + prefix + b"\x00\x00"
    root = _miner_tx_root(full, len(header), len(full)-2)
    hashing = header + root + b"\x01"
    reserved = len(header)+len(prefix)-8
    return validate_template({"result": {
        "height": 1, "difficulty": 1, "expected_reward": 1,
        "seed_hash": "ab"*32, "blocktemplate_blob": full.hex(),
        "blockhashing_blob": hashing.hex(), "reserved_offset": reserved,
    }})


class ReservedCandidateTests(unittest.TestCase):
    def test_keccak_256_reference_vectors(self):
        self.assertEqual(keccak_256(b"").hex(),
                         "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")
        self.assertEqual(keccak_256(b"abc").hex(),
                         "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45")

    def test_updates_exact_nonce_and_reserved_bytes_and_hash_tree(self):
        original = fixture()
        result = build_reserved_candidate(original, reserve_hex="1122334455667788",
                                           nonce_hex="01020304")
        self.assertEqual(result.nonce_offset, 35)
        self.assertEqual(result.full_block_blob[result.nonce_offset:result.nonce_offset+4],
                         bytes.fromhex("01020304"))
        self.assertEqual(result.full_block_blob[result.reserved_offset:result.reserved_offset+8],
                         bytes.fromhex("1122334455667788"))
        for pos, (before, after) in enumerate(zip(original.blocktemplate_blob, result.full_block_blob)):
            if pos not in {*range(35, 39), *range(result.reserved_offset, result.reserved_offset+8)}:
                self.assertEqual(before, after)
        self.assertNotEqual(result.tree_root, original.blockhashing_blob[39:71])
        self.assertEqual(result.hashing_blob, result.full_block_blob[:39]+result.tree_root+b"\x01")
        self.assertEqual(result.tree_root,
                         _miner_tx_root(result.full_block_blob, 39, len(result.full_block_blob)-2))

    def test_reject_invalid_or_unchanged_reserve_and_nonce(self):
        original = fixture()
        for reserve in ("00"*8, "11", "zz"*8, 10, None):
            with self.subTest(reserve=reserve), self.assertRaises(VerificationError):
                build_reserved_candidate(original,reserve_hex=reserve,nonce_hex="01020304")
        for nonce in ("", "01", "zzzzzzzz", None):
            with self.subTest(nonce=nonce), self.assertRaises(VerificationError):
                build_reserved_candidate(original,reserve_hex="11"*8,nonce_hex=nonce)

    def test_fail_closed_on_nonisolated_templates_and_tree_mismatch(self):
        original = fixture()
        changes = (
            replace(original,height=2),
            replace(original,difficulty=2),
            replace(original,reserved_offset=original.reserved_offset-2),
            replace(original,blockhashing_blob=original.blockhashing_blob[:39]+bytes(32)+b"\x01"),
            replace(original,blockhashing_blob=original.blockhashing_blob[:-1]+b"\x02"),
            replace(original,blocktemplate_blob=original.blocktemplate_blob[:-1]+b"\x01"),
            replace(original,blocktemplate_blob=original.blocktemplate_blob[:35]+b"\x01"+original.blocktemplate_blob[36:]),
        )
        for changed in changes:
            with self.subTest(changed=changed), self.assertRaises(VerificationError):
                build_reserved_candidate(changed,reserve_hex="11"*8,nonce_hex="01020304")


if __name__ == "__main__":
    unittest.main()
