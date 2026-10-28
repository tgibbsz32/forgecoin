#!/usr/bin/env python3
"""Purely synthetic offline inventory reconciliation tests."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from reconcile_mfrg_token_accounts import InventoryError, parse_inventory, reconcile_inventory, main
from test_verify_mfrg_mint_snapshot import FAKE_MINT, fake_rpc, OTHER_FAKE_KEY
from verify_mfrg_mint_snapshot import TOKEN_PROGRAM

FIRST_ACCOUNT = OTHER_FAKE_KEY
SECOND_ACCOUNT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
OWNER_A = "11111111111111111111111111111111"
OWNER_B = TOKEN_PROGRAM
AMOUNTS = (300_000_000_000_000, 200_000_000_000_000)


def token(address, owner, raw, mint=FAKE_MINT, state="initialized", delegate=None,
          delegated_raw=0, close_authority=None):
    info = {
        "mint": mint,
        "owner": owner,
        "state": state,
        "isNative": False,
        "tokenAmount": {"amount": str(raw), "decimals": 6, "uiAmount": None},
    }
    if delegate is not None:
        info["delegate"] = delegate
        info["delegatedAmount"] = {
            "amount": str(delegated_raw), "decimals": 6, "uiAmount": None,
        }
    if close_authority is not None:
        info["closeAuthority"] = close_authority
    return {
        "pubkey": address,
        "account": {
            "owner": TOKEN_PROGRAM, "executable": False,
            "data": {"program": "spl-token",
                     "parsed": {"type": "account", "info": info}}
        },
    }


def inventory(slot=123456792):
    return {
        "jsonrpc": "2.0",
        "id": FAKE_MINT + ":inventory",
        "result": {
            "context": {"slot": slot},
            "value": [token(FIRST_ACCOUNT, OWNER_A, AMOUNTS[0]),
                      token(SECOND_ACCOUNT, OWNER_B, AMOUNTS[1])],
        },
    }


def compare(a=None, b=None, mint=None):
    return reconcile_inventory(
        FAKE_MINT, mint if mint is not None else fake_rpc(),
        a if a is not None else inventory(),
        b if b is not None else inventory(slot=123456793),
        "https://first.example.org", "https://second.example.org",
    )


class TokenAccountInventoryTests(unittest.TestCase):
    def test_01_two_sources_reconcile_without_claiming_mainnet_provenance(self):
        r = compare()
        self.assertTrue(r["offline_consistency_passed"])
        self.assertEqual(r["listed_token_accounts"], 2)
        self.assertEqual(r["distinct_owner_addresses"], 2)
        self.assertEqual(r["listed_balance_total_atomic"], "500000000000000")
        for key in ("rpc_provenance_authenticated", "scan_filter_and_completeness_proven",
                    "live_chain_state_verified", "beneficial_owner_or_treasury_identity_proven",
                    "founder_vesting_funded_or_deployed", "sale_or_issuance_authorized"):
            self.assertFalse(r[key], key)

    def test_02_account_order_does_not_change_holdings(self):
        b = inventory(slot=123456793)
        b["result"]["value"].reverse()
        self.assertTrue(compare(b=b)["matching_listed_account_records"])

    def test_03_missing_nonzero_account_fails(self):
        b = inventory(slot=123456793)
        b["result"]["value"].pop()
        with self.assertRaisesRegex(InventoryError, "Different token account sets"):
            compare(b=b)

    def test_04_conflicting_balance_fails(self):
        b = inventory(slot=123456793)
        b["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"] = str(AMOUNTS[0] - 1)
        with self.assertRaises(InventoryError):
            compare(b=b)

    def test_05_consistent_but_incomplete_account_sum_fails(self):
        a = inventory()
        b = inventory(slot=123456793)
        for snap in (a, b):
            snap["result"]["value"].pop()
        with self.assertRaisesRegex(InventoryError, "does not match mint supply"):
            compare(a=a, b=b)

    def test_06_account_duplication_fails(self):
        a = inventory()
        a["result"]["value"].append(copy.deepcopy(a["result"]["value"][0]))
        with self.assertRaisesRegex(InventoryError, "Duplicate token account"):
            compare(a=a)

    def test_07_mismatched_mint_fails(self):
        a = inventory()
        a["result"]["value"][0]["account"]["data"]["parsed"]["info"]["mint"] = SECOND_ACCOUNT
        with self.assertRaisesRegex(InventoryError, "Cross-mint"):
            compare(a=a)

    def test_08_token_program_and_type_required(self):
        for field, value in (("owner", OWNER_A), ("executable", True)):
            a = inventory()
            a["result"]["value"][0]["account"][field] = value
            with self.subTest(field=field), self.assertRaises(InventoryError):
                compare(a=a)
        a = inventory()
        a["result"]["value"][0]["account"]["data"]["parsed"]["type"] = "mint"
        with self.assertRaises(InventoryError):
            compare(a=a)

    def test_09_6_decimal_integer_amount_required(self):
        for amount in ("1e10", "-1", 42, True, "18446744073709551616"):
            a = inventory()
            a["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"] = amount
            with self.subTest(amount=amount), self.assertRaises(InventoryError):
                compare(a=a)
        a = inventory()
        a["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["decimals"] = 9
        with self.assertRaises(InventoryError):
            compare(a=a)

    def test_10_delegates_are_not_double_counted(self):
        a = inventory()
        b = inventory(slot=123456793)
        for snap in (a, b):
            info = snap["result"]["value"][0]["account"]["data"]["parsed"]["info"]
            info["delegate"] = SECOND_ACCOUNT
            info["delegatedAmount"] = {"amount": "100000000000", "decimals": 6}
        r = compare(a=a, b=b)
        self.assertEqual(r["listed_balance_total_atomic"], "500000000000000")
        self.assertEqual(r["delegated_token_accounts"], 1)

    def test_11_delegation_disagreement_rejected(self):
        a = inventory()
        info = a["result"]["value"][0]["account"]["data"]["parsed"]["info"]
        info["delegate"] = SECOND_ACCOUNT
        info["delegatedAmount"] = {"amount": "1", "decimals": 6}
        with self.assertRaisesRegex(InventoryError, "authorities"):
            compare(a=a)

    def test_12_delegated_amount_cannot_exceed_balance(self):
        a = inventory()
        info = a["result"]["value"][0]["account"]["data"]["parsed"]["info"]
        info["delegate"] = SECOND_ACCOUNT
        info["delegatedAmount"] = {"amount": str(AMOUNTS[0]+1), "decimals": 6}
        with self.assertRaises(InventoryError):
            compare(a=a)

    def test_13_frozen_account_is_counted_and_reported(self):
        a, b = inventory(), inventory(slot=123456793)
        for snap in (a, b):
            snap["result"]["value"][0]["account"]["data"]["parsed"]["info"]["state"] = "frozen"
        r = compare(a=a, b=b)
        self.assertEqual(r["frozen_token_accounts"], 1)
        self.assertEqual(r["listed_balance_total_atomic"], "500000000000000")

    def test_14_close_authority_difference_blocks(self):
        a = inventory()
        a["result"]["value"][0]["account"]["data"]["parsed"]["info"]["closeAuthority"] = SECOND_ACCOUNT
        with self.assertRaises(InventoryError):
            compare(a=a)

    def test_15_snapshot_slot_gap_blocks(self):
        a = inventory(slot=123460000)
        with self.assertRaisesRegex(InventoryError, "slots too far"):
            compare(a=a)

    def test_16_wrong_rpc_id_or_no_context_blocks(self):
        a = inventory()
        a["id"] = "wrong"
        with self.assertRaisesRegex(InventoryError, "RPC id"):
            compare(a=a)
        a = inventory()
        a["result"] = a["result"]["value"]
        with self.assertRaises(InventoryError):
            compare(a=a)

    def test_17_same_claimed_provider_host_blocks(self):
        with self.assertRaisesRegex(InventoryError, "Distinct claimed"):
            reconcile_inventory(
                FAKE_MINT, fake_rpc(), inventory(), inventory(slot=123456793),
                "https://FIRST.example.org", "https://first.example.org"
            )

    def test_18_mint_authority_observed_does_not_imply_holder_control(self):
        r = compare(mint=fake_rpc(mint_authority=SECOND_ACCOUNT))
        self.assertEqual(r["mint_authority_from_snapshot"], SECOND_ACCOUNT)
        self.assertFalse(r["beneficial_owner_or_treasury_identity_proven"])

    def test_19_tampering_with_mint_supply_is_detected(self):
        with self.assertRaises(InventoryError):
            compare(mint=fake_rpc(supply=400000000000000))

    def test_20_cli_is_offline_and_accepts_powershell_bom(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            mint_path, first, second = [base / f for f in ("mint.json", "accounts1.json", "accounts2.json")]
            mint_path.write_text(json.dumps(fake_rpc()), encoding="utf-8")
            first.write_bytes(bytes([0xef, 0xbb, 0xbf]) + json.dumps(inventory()).encode("utf-8"))
            second.write_text(json.dumps(inventory(slot=123456793)), encoding="utf-8")
            args = [
                "--mint", FAKE_MINT, "--mint-json", str(mint_path),
                "--first-accounts", str(first), "--second-accounts", str(second),
                "--first-origin", "https://first.example.org",
                "--second-origin", "https://second.example.org"
            ]
            self.assertEqual(main(args), 0)
            second.write_text(json.dumps(inventory(slot=123456793)["result"]), encoding="utf-8")
            self.assertEqual(main(args), 2)

    def test_21_zero_supply_empty_inventory_reconciles_as_unverified(self):
        a = inventory()
        b = inventory(slot=123456793)
        a["result"]["value"] = []
        b["result"]["value"] = []
        r = compare(a=a, b=b, mint=fake_rpc(supply=0))
        self.assertEqual(r["listed_balance_total_atomic"], "0")
        self.assertFalse(r["live_chain_state_verified"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
