"""Exact public-key extraction from the selected frozen FRG genesis.

Offline only. Does not know or generate any genesis spend authorization.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from extract_frozen_genesis_output_key import extract_genesis_pubkey, uvarint


class FrozenGenesisPublicOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "config/mainnet.identity.json").read_text(encoding="utf-8"))

    def test_byte_exact_known_public_genesis_output(self):
        self.assertEqual(
            extract_genesis_pubkey(self.manifest),
            "b595d1f9b584153125490337444ba18d842151ed8dc4586a1d9d1fb06a69002a",
        )
        self.assertEqual(self.manifest["currency"]["genesis_output_atomic"], 1192092895)

    def test_reject_noncanonical_or_truncated_varint(self):
        for data in (b"\x80", b"\x80\x00", b"\xff" * 11):
            with self.subTest(data=data), self.assertRaises(ValueError):
                uvarint(data, 0)

    def test_genesis_identity_and_structure_changes_fail_closed(self):
        variants = (
            ("release_authorized", True),
            ("genesis_nonce", 20261020),
            ("genesis_hash", "0" * 64),
            ("genesis_tx_hex", "zz"),
            ("genesis_tx_hex", self.manifest["genesis_tx_hex"][:-2]),
            ("genesis_tx_hex", "02" + self.manifest["genesis_tx_hex"][2:]),
            ("genesis_tx_hex", self.manifest["genesis_tx_hex"] + "00"),
        )
        for key, value in variants:
            bad = deepcopy(self.manifest)
            bad[key] = value
            with self.subTest(key=key, value=str(value)[:15]), self.assertRaises(ValueError):
                extract_genesis_pubkey(bad)

    def test_genesis_output_amount_must_match_manifest(self):
        bad = deepcopy(self.manifest)
        bad["currency"]["genesis_output_atomic"] = 0
        with self.assertRaisesRegex(ValueError, "structure"):
            extract_genesis_pubkey(bad)


if __name__ == "__main__":
    unittest.main()
