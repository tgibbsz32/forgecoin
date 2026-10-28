#!/usr/bin/env python3
"""Self-contained synthetic-RPC mint parser tests; no real addresses queried."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from verify_mfrg_mint_snapshot import (
    TOKEN_PROGRAM, TARGET_ATOMIC, DEVNET_TEST_MINT,
    SnapshotError, assess_snapshot, main
)

# This is the System Program ID, deliberately NOT a real test mFRG mint.
# Our fixtures are synthetic and cannot authenticate any Solana mint.
FAKE_MINT = "11111111111111111111111111111111"
OTHER_FAKE_KEY = "2xLoLobNEk39Vne4FhG91i2j14Pxq75M4RAt4Pvwrk26"


def fake_rpc(supply=TARGET_ATOMIC, mint_authority=None, freeze_authority=None):
    return {
        "jsonrpc": "2.0", "id": FAKE_MINT,
        "result": {
            "context": {"slot": 123456789, "apiVersion": "synthetic-fixture"},
            "value": {
                "owner": TOKEN_PROGRAM, "executable": False,
                "data": {
                    "program": "spl-token",
                    "parsed": {
                        "type": "mint",
                        "info": {
                            "decimals": 6, "isInitialized": True,
                            "supply": str(supply),
                            "mintAuthority": mint_authority,
                            "freezeAuthority": freeze_authority,
                        },
                    },
                },
            },
        },
    }


class SnapshotParserTests(unittest.TestCase):
    def test_fixed_exactly_500m_only_reports_self_consistency(self):
        r = assess_snapshot(FAKE_MINT, fake_rpc())
        self.assertTrue(r["snapshot_self_consistent"])
        self.assertEqual(r["raw_supply_atomic"], "500000000000000")
        self.assertEqual(r["supply_mfrg"], "500000000.000000")
        self.assertEqual(r["decision"], "SNAPSHOT_SUGGESTS_FIXED_SUPPLY_AT_TARGET")
        self.assertIs(r["independently_authenticated_mainnet"], False)
        self.assertIs(r["issuer_or_founder_ownership_proven"], False)
        self.assertIs(r["sale_or_issuance_authorized"], False)

    def test_fixed_below_target_requires_migration_review(self):
        r = assess_snapshot(FAKE_MINT, fake_rpc(50_000_000 * 1_000_000))
        self.assertEqual(r["decision"], "SNAPSHOT_SUGGESTS_IRREVOCABLE_SUPPLY_BELOW_TARGET")
        self.assertFalse(r["supply_reissuance_possible_under_observed_authority"])

    def test_mint_authority_present_blocks_fixed_supply_claim(self):
        r = assess_snapshot(FAKE_MINT, fake_rpc(mint_authority=OTHER_FAKE_KEY))
        self.assertEqual(r["decision"], "AT_TARGET_BUT_MINT_AUTHORITY_STILL_ACTIVE")
        self.assertFalse(r["fixed_supply_in_snapshot"])

    def test_lower_supply_with_authority_is_not_yet_final(self):
        r = assess_snapshot(FAKE_MINT, fake_rpc(0, mint_authority=OTHER_FAKE_KEY))
        self.assertEqual(r["decision"], "BELOW_TARGET_AND_MINT_AUTHORITY_ACTIVE")

    def test_freeze_authority_disclosed_not_ignored(self):
        r = assess_snapshot(FAKE_MINT, fake_rpc(freeze_authority=OTHER_FAKE_KEY))
        self.assertEqual(r["freeze_authority"], OTHER_FAKE_KEY)
        self.assertIsNone(r["mint_authority"])

    def test_more_than_policy_max_fails(self):
        with self.assertRaises(SnapshotError):
            assess_snapshot(FAKE_MINT, fake_rpc(TARGET_ATOMIC + 1))

    def test_devnet_address_rejected_as_mainnet(self):
        with self.assertRaises(SnapshotError):
            assess_snapshot(DEVNET_TEST_MINT, fake_rpc())

    def test_wrong_mint_rpc_id_fails(self):
        x = fake_rpc()
        x["id"] = "other"
        with self.assertRaises(SnapshotError):
            assess_snapshot(FAKE_MINT, x)

    def test_missing_account_does_not_imply_zero_supply(self):
        x = fake_rpc()
        x["result"]["value"] = None
        with self.assertRaises(SnapshotError):
            assess_snapshot(FAKE_MINT, x)

    def test_reject_token_2022_and_non_mint_accounts(self):
        for attr, value in (("owner", "TokenzQdBNbLqP5VEhdkAS6EPF9sJFiD4aH3M13fkh"),
                            ("executable", True)):
            x = fake_rpc()
            x["result"]["value"][attr] = value
            with self.subTest(attr=attr), self.assertRaises(SnapshotError):
                assess_snapshot(FAKE_MINT, x)
        x = fake_rpc()
        x["result"]["value"]["data"]["parsed"]["type"] = "account"
        with self.assertRaises(SnapshotError):
            assess_snapshot(FAKE_MINT, x)

    def test_decimals_and_initialization_required(self):
        for bad_decimals in (0, 9, "6", True):
            x = fake_rpc()
            x["result"]["value"]["data"]["parsed"]["info"]["decimals"] = bad_decimals
            with self.subTest(decimals=bad_decimals), self.assertRaises(SnapshotError):
                assess_snapshot(FAKE_MINT, x)
        x = fake_rpc()
        x["result"]["value"]["data"]["parsed"]["info"]["isInitialized"] = False
        with self.assertRaises(SnapshotError):
            assess_snapshot(FAKE_MINT, x)

    def test_reject_invalid_supply_and_authority(self):
        for bad in (-1, 12.4, "1e9", "nan", True):
            x = fake_rpc()
            x["result"]["value"]["data"]["parsed"]["info"]["supply"] = bad
            with self.subTest(supply=bad), self.assertRaises(SnapshotError):
                assess_snapshot(FAKE_MINT, x)
        x = fake_rpc()
        x["result"]["value"]["data"]["parsed"]["info"]["mintAuthority"] = "not-a-key"
        with self.assertRaises(SnapshotError):
            assess_snapshot(FAKE_MINT, x)

    def test_missing_authority_field_cannot_be_called_revoked(self):
        for name in ("mintAuthority", "freezeAuthority"):
            x = fake_rpc()
            del x["result"]["value"]["data"]["parsed"]["info"][name]
            with self.subTest(field=name), self.assertRaises(SnapshotError):
                assess_snapshot(FAKE_MINT, x)

    def test_context_slot_required(self):
        for bad in (0, -1, "123", True):
            x = fake_rpc()
            x["result"]["context"]["slot"] = bad
            with self.subTest(slot=bad), self.assertRaises(SnapshotError):
                assess_snapshot(FAKE_MINT, x)

    def test_cli_read_only_success_and_failure(self):
        with tempfile.TemporaryDirectory(prefix="mfrg-fake-rpc-") as d:
            p = Path(d) / "synthetic-snapshot.json"
            p.write_text(json.dumps(fake_rpc()), encoding="utf-8")
            self.assertEqual(main(["--mint", FAKE_MINT, "--rpc-json", str(p)]), 0)
            # Windows PowerShell 5.1 defaults to a UTF-8 BOM for Set-Content.
            p.write_bytes(bytes([0xef, 0xbb, 0xbf]) + json.dumps(fake_rpc()).encode("utf-8"))
            self.assertEqual(main(["--mint", FAKE_MINT, "--rpc-json", str(p)]), 0)
            p.write_text(json.dumps(fake_rpc(TARGET_ATOMIC + 1)), encoding="utf-8")
            self.assertEqual(main(["--mint", FAKE_MINT, "--rpc-json", str(p)]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
