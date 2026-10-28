#!/usr/bin/env python3
"""No live network calls: synthetic test doubles for Step 16 mainnet RPC gate."""
import copy
import unittest

from read_mfrg_mainnet_provenance import (
    MAINNET_GENESIS, LiveReadError, assess, exact_https_origin, rpc_call
)
from test_verify_mfrg_mint_initialization import FAKE_SIG, FAKE_MINT, tx
from test_verify_mfrg_mint_snapshot import fake_rpc, OTHER_FAKE_KEY

URL_A = "https://alpha.example.org"
URL_B = "https://beta.example.net"


def make_mock(*, genesis=MAINNET_GENESIS, supply_delta=0, wrong_mint=False,
              bad_tx=False, errors=None, identical_accounts=False,
              uninitialized=False):
    calls = []
    errors = errors or {}
    def fake_transport(host, method, params, reqid):
        calls.append((host, method, params, reqid))
        if (host, method) in errors:
            raise LiveReadError(errors[(host,method)])
        if method == "getGenesisHash":
            return {"jsonrpc": "2.0", "id": reqid, "result": (
                genesis if host=="alpha.example.org" else MAINNET_GENESIS)}
        if method == "getAccountInfo":
            response = fake_rpc(supply=500_000_000_000_000 + (
                supply_delta if host=="beta.example.net" else 0))
            if host == "beta.example.net" and not identical_accounts:
                response["result"]["context"]["slot"] += 3
            if wrong_mint:
                response["id"] = "other"
            return response
        if method == "getTransaction":
            response = tx(slot=120_000_000)
            if bad_tx:
                response["result"]["meta"]["err"] = {"InstructionError":[0,"InvalidAccountData"]}
            if uninitialized:
                response["result"]["transaction"]["message"]["instructions"] = []
            return response
        raise AssertionError("Unexpected RPC: "+method)
    return fake_transport, calls


class GenesisAndMintLiveReadTests(unittest.TestCase):
    def run_assessment(self, mock, mint=FAKE_MINT, signature=FAKE_SIG):
        return assess(mint, signature, URL_A, URL_B, rpc=mock)

    def test_01_consistent_mainnet_genesis_and_mint_parsed_read(self):
        rpc, calls = make_mock()
        report = self.run_assessment(rpc)
        self.assertTrue(report["genesis_matches_mainnet_expected_on_both_rpc_endpoints"])
        self.assertTrue(report["read_only_rpc_queries_succeeded"])
        self.assertEqual(report["mint_supply_atomic"], "500000000000000")
        self.assertEqual(report["mint_initialization_slot"], 120000000)
        self.assertEqual(len(calls), 6)
        self.assertEqual([x[1] for x in calls], [
            "getGenesisHash","getAccountInfo","getTransaction",
            "getGenesisHash","getAccountInfo","getTransaction"])
        for state in ("cryptographic_transaction_signature_verified",
                      "operator_provider_independence_proven",
                      "project_issuer_and_beneficial_owner_verified",
                      "treasury_custody_or_funding_verified","sale_or_issuance_authorized"):
            self.assertIs(report[state], False, state)

    def test_02_wrong_genesis_stops_before_mint_lookup(self):
        rpc, calls = make_mock(genesis="EtWTRABZaYq6iMfeYKouRu166VU2xqa1wcaWoxPkrZBG")
        with self.assertRaisesRegex(LiveReadError, "genesis"):
            self.run_assessment(rpc)
        self.assertEqual([c[1] for c in calls], ["getGenesisHash"])

    def test_03_supply_conflict_fails_closed(self):
        rpc, _ = make_mock(supply_delta=-1)
        with self.assertRaises(LiveReadError):
            self.run_assessment(rpc)

    def test_04_unsigned_wrong_mint_reply_rejected(self):
        rpc,_ = make_mock(wrong_mint=True)
        with self.assertRaises(LiveReadError):
            self.run_assessment(rpc)

    def test_05_failed_transaction_rejected(self):
        rpc,_ = make_mock(bad_tx=True)
        with self.assertRaises(LiveReadError):
            self.run_assessment(rpc)

    def test_06_missing_initialize_mint_instruction_rejected(self):
        rpc,_ = make_mock(uninitialized=True)
        with self.assertRaises(LiveReadError):
            self.run_assessment(rpc)

    def test_07_reject_devnet_test_mint(self):
        rpc, calls=make_mock()
        with self.assertRaisesRegex(LiveReadError,"devnet"):
            self.run_assessment(rpc,mint="9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw")
        self.assertEqual(calls,[])

    def test_08_reject_invalid_signature_before_requests(self):
        rpc,calls=make_mock()
        with self.assertRaises(LiveReadError):
            self.run_assessment(rpc,signature="not-a-signature")
        self.assertEqual(calls,[])

    def test_09_reject_identical_provider_hosts(self):
        rpc,calls=make_mock()
        with self.assertRaisesRegex(LiveReadError,"distinct"):
            assess(FAKE_MINT,FAKE_SIG,URL_A,"https://ALPHA.EXAMPLE.ORG/",rpc=rpc)
        self.assertEqual(calls,[])

    def test_10_only_public_https_hostnames_permitted(self):
        for bad in ("http://example.org","https://user:key@example.org",
                    "https://example.org/path","https://example.org/?token=secret",
                    "https://localhost","https://127.0.0.1","https://10.1.2.3",
                    "https://169.254.169.254","https://192.168.1.1",
                    "https://example.org:8443","ftp://example.org"):
            with self.subTest(url=bad),self.assertRaises(LiveReadError):
                exact_https_origin(bad)

    def test_11_normalize_public_https_hostname(self):
        self.assertEqual(exact_https_origin("https://RPC.EXAMPLE.ORG:443/"),"rpc.example.org")

    def test_12_rpc_errors_stop_following_calls(self):
        rpc,calls=make_mock(errors={("alpha.example.org","getAccountInfo"):"provider unavailable"})
        with self.assertRaisesRegex(LiveReadError,"provider unavailable"):
            self.run_assessment(rpc)
        self.assertEqual([c[1] for c in calls],["getGenesisHash","getAccountInfo"])

    def test_13_same_snapshot_document_conservatively_rejected(self):
        rpc,_=make_mock(identical_accounts=True)
        with self.assertRaises(LiveReadError):
            self.run_assessment(rpc)

    def test_14_wrong_signer_or_mint_no_live_data_claim(self):
        rpc, calls=make_mock()
        with self.assertRaises(LiveReadError):
            self.run_assessment(rpc,mint="11111111111111111111111111111112")
        self.assertTrue(calls)

    def test_15_mainnet_hash_is_expected_network_constant(self):
        self.assertEqual(MAINNET_GENESIS,"5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d")


if __name__ == "__main__":
    unittest.main(verbosity=2)
