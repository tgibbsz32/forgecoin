#!/usr/bin/env python3
"""Synthetic transport tests; never contact a real Solana RPC endpoint."""
from __future__ import annotations

import copy
import unittest

from read_mfrg_mainnet_inventory import (
    assess, account_params, LiveReadError, main,
)
from read_mfrg_mainnet_provenance import MAINNET_GENESIS
from test_verify_mfrg_mint_initialization import FAKE_MINT, FAKE_SIG, tx
from test_verify_mfrg_mint_snapshot import fake_rpc, OTHER_FAKE_KEY
from test_reconcile_mfrg_token_accounts import inventory
from verify_mfrg_mint_snapshot import TOKEN_PROGRAM

A = "https://alpha.example.org"
B = "https://beta.example.net"


def fake_transport_factory(*, bad_genesis=None, bad_tx=False, conflict_supply=False,
                           missing_account=False, wrong_mint=False,
                           stale=False, unsafe_account=False, duplicate=False,
                           malformed=False, oversupply=False, identical=False,
                           unexpected_error=None):
    calls = []
    def rpc(host, method, params, reqid):
        calls.append((host, method, params, reqid))
        n = sum(1 for h, m, *_ in calls if h == host and m == "getAccountInfo")
        is_second = host == "beta.example.net"
        if unexpected_error and method == unexpected_error:
            raise LiveReadError("Mock RPC service unavailable")
        if method == "getGenesisHash":
            return {"jsonrpc": "2.0", "id": reqid,
                    "result": bad_genesis if bad_genesis and is_second else MAINNET_GENESIS}
        if method == "getTransaction":
            response = tx(slot=120_000_000)
            if bad_tx:
                response["result"]["meta"]["err"] = {"InstructionError": [0, "InvalidAccountData"]}
            return response
        if method == "getAccountInfo":
            delta = 1 if is_second else 0
            slot = 123456789 + (delta * 4)
            if n > 1:
                slot += 10
            response = fake_rpc(supply=(500_000_000_000_000 -
                                       (1 if conflict_supply and is_second else 0)))
            response["result"]["context"]["slot"] = slot
            if wrong_mint:
                response["id"] = "wrong"
            if oversupply and n > 1:
                response["result"]["value"]["data"]["parsed"]["info"]["supply"] = "500000000000001"
            return response
        if method == "getProgramAccounts":
            response = inventory(slot=123456799 + (0 if identical or not is_second else 4))
            if stale and is_second:
                response["result"]["context"]["slot"] += 2000
            if missing_account and is_second:
                response["result"]["value"].pop()
            if unsafe_account and is_second:
                response["result"]["value"][0]["account"]["data"]["parsed"]["info"]["delegate"] = OTHER_FAKE_KEY
                response["result"]["value"][0]["account"]["data"]["parsed"]["info"]["delegatedAmount"] = {
                    "amount": "5", "decimals": 6
                }
            if duplicate and is_second:
                response["result"]["value"].append(copy.deepcopy(response["result"]["value"][0]))
            if malformed and is_second:
                response["result"]["value"][0]["account"]["owner"] = "11111111111111111111111111111111"
            return response
        raise AssertionError("Unexpected RPC method " + method)
    return rpc, calls


class MainnetInventoryReadTests(unittest.TestCase):
    def test_01_ten_readonly_queries_check_filtered_accounts(self):
        rpc, calls = fake_transport_factory()
        result = assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)
        self.assertEqual(len(calls), 10)
        self.assertEqual([item[1] for item in calls], [
            "getGenesisHash", "getAccountInfo", "getTransaction",
            "getGenesisHash", "getAccountInfo", "getTransaction",
            "getAccountInfo", "getProgramAccounts",
            "getAccountInfo", "getProgramAccounts",
        ])
        self.assertEqual(result["matching_raw_supply_atomic"], "500000000000000")
        self.assertEqual(result["listed_token_accounts"], 2)
        self.assertTrue(result["live_readonly_rpc_consistency_passed"])
        self.assertEqual(result["mint_initialization_slot"], 120_000_000)
        for name in ("rpc_answers_cryptographically_authenticated",
                     "rpc_provider_independence_proven",
                     "transaction_signature_cryptographically_verified",
                     "account_scan_completeness_independently_proven",
                     "project_mint_issuer_or_beneficial_owner_verified",
                     "nine_treasury_account_ownership_verified",
                     "founder_vesting_deployed_or_funded",
                     "sale_or_issuance_authorized"):
            self.assertIs(result[name], False, name)
        for host, method, params, reqid in calls:
            self.assertIn(method, ("getGenesisHash", "getAccountInfo", "getTransaction", "getProgramAccounts"))
            if method == "getProgramAccounts":
                self.assertEqual(params, account_params(FAKE_MINT))
                self.assertEqual(params[0], TOKEN_PROGRAM)
                self.assertEqual(params[1]["filters"], [
                    {"dataSize": 165}, {"memcmp": {"offset": 0, "bytes": FAKE_MINT}}
                ])

    def test_02_wrong_genesis_blocks_any_account_scan(self):
        rpc, calls = fake_transport_factory(bad_genesis="wrong")
        with self.assertRaisesRegex(LiveReadError, "genesis"):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)
        self.assertFalse(any(method == "getProgramAccounts" for _, method, *_ in calls))

    def test_03_devnet_address_rejected_without_network_io(self):
        rpc, calls = fake_transport_factory()
        with self.assertRaisesRegex(LiveReadError, "devnet"):
            assess("9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw", FAKE_SIG, A, B, rpc=rpc)
        self.assertEqual(calls, [])

    def test_04_unknown_creation_signature_rejected_without_network_io(self):
        rpc, calls = fake_transport_factory()
        with self.assertRaises(LiveReadError):
            assess(FAKE_MINT, "not-a-signature", A, B, rpc=rpc)
        self.assertEqual(calls, [])

    def test_05_failed_initialization_transaction_stops_scanning(self):
        rpc, calls = fake_transport_factory(bad_tx=True)
        with self.assertRaises(LiveReadError):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)
        self.assertFalse(any(method == "getProgramAccounts" for _, method, *_ in calls))

    def test_06_conflicting_provider_supply_stops_scanning(self):
        rpc, calls = fake_transport_factory(conflict_supply=True)
        with self.assertRaises(LiveReadError):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)
        self.assertFalse(any(method == "getProgramAccounts" for _, method, *_ in calls))

    def test_07_one_missing_nonzero_account_blocks_report(self):
        rpc, _ = fake_transport_factory(missing_account=True)
        with self.assertRaisesRegex(LiveReadError, "inventory"):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)

    def test_08_wrong_mint_identity_does_not_verify(self):
        rpc, _ = fake_transport_factory(wrong_mint=True)
        with self.assertRaises(LiveReadError):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)

    def test_09_stale_slot_gap_rejected(self):
        rpc, _ = fake_transport_factory(stale=True)
        with self.assertRaisesRegex(LiveReadError, "slots too far|slot gap"):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)

    def test_10_changed_delegate_between_provider_snapshots_rejected(self):
        rpc, _ = fake_transport_factory(unsafe_account=True)
        with self.assertRaisesRegex(LiveReadError, "authorities|delegation"):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)

    def test_11_duplicate_token_account_rejected(self):
        rpc, _ = fake_transport_factory(duplicate=True)
        with self.assertRaisesRegex(LiveReadError, "Duplicate"):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)

    def test_12_malformed_program_account_rejected(self):
        rpc, _ = fake_transport_factory(malformed=True)
        with self.assertRaisesRegex(LiveReadError, "program owner"):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)

    def test_13_oversupply_on_refreshed_mint_snapshot_rejected(self):
        rpc, _ = fake_transport_factory(oversupply=True)
        with self.assertRaises(LiveReadError):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)

    def test_14_identical_provider_host_rejected(self):
        rpc, calls = fake_transport_factory()
        with self.assertRaisesRegex(LiveReadError, "distinct"):
            assess(FAKE_MINT, FAKE_SIG, A, "https://ALPHA.EXAMPLE.ORG/", rpc=rpc)
        self.assertEqual(calls, [])

    def test_15_provider_failure_rejects_no_partial_success(self):
        rpc, _ = fake_transport_factory(unexpected_error="getProgramAccounts")
        with self.assertRaisesRegex(LiveReadError, "unavailable"):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)

    def test_16_identical_account_snapshots_conservatively_rejected(self):
        rpc, _ = fake_transport_factory(identical=True)
        with self.assertRaisesRegex(LiveReadError, "Identical"):
            assess(FAKE_MINT, FAKE_SIG, A, B, rpc=rpc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
