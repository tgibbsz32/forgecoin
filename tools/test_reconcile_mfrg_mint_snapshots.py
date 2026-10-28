#!/usr/bin/env python3
"""Synthetic, offline comparison tests; never contact Solana or use real keys."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from reconcile_mfrg_mint_snapshots import (
    ReconciliationError, claimed_host, main, reconcile,
)
from test_verify_mfrg_mint_snapshot import FAKE_MINT, OTHER_FAKE_KEY, fake_rpc


def two():
    a, b = fake_rpc(), fake_rpc()
    b["result"]["context"]["slot"] += 10
    return a, b


class IndependentMintComparisonTests(unittest.TestCase):
    def compare(self, a, b):
        return reconcile(FAKE_MINT, a, b,
                         "https://api.mainnet-beta.solana.com",
                         "https://another-rpc.example.org")

    def test_01_matching_snapshots_still_not_mainnet_verified(self):
        first, second = two()
        out = self.compare(first, second)
        self.assertTrue(out["offline_comparison_passed"])
        self.assertEqual(out["matching_raw_supply_atomic"], "500000000000000")
        self.assertEqual(out["matching_policy_classification"],
                         "SNAPSHOT_SUGGESTS_FIXED_SUPPLY_AT_TARGET")
        for name in ("rpc_provenance_authenticated", "independent_network_sources_proven",
                     "mint_ownership_proven", "account_holdings_reconciled",
                     "treasury_funding_proven", "founder_vesting_deployed",
                     "sale_or_issuance_authorized"):
            self.assertIs(out[name], False)
        self.assertEqual(len(out["sha256_evidence"]), 2)
        self.assertNotEqual(*out["sha256_evidence"])

    def test_02_identical_documents_rejected_as_independent(self):
        a = fake_rpc()
        with self.assertRaises(ReconciliationError):
            self.compare(a, copy.deepcopy(a))

    def test_03_conflicting_supply_rejected(self):
        a, b = two()
        b["result"]["value"]["data"]["parsed"]["info"]["supply"] = str(499999999000000)
        with self.assertRaisesRegex(ReconciliationError, "raw_supply_atomic"):
            self.compare(a, b)

    def test_04_conflicting_mint_authority_rejected(self):
        a, b = two()
        b["result"]["value"]["data"]["parsed"]["info"]["mintAuthority"] = OTHER_FAKE_KEY
        with self.assertRaisesRegex(ReconciliationError, "mint_authority"):
            self.compare(a, b)

    def test_05_conflicting_freeze_authority_rejected(self):
        a, b = two()
        b["result"]["value"]["data"]["parsed"]["info"]["freezeAuthority"] = OTHER_FAKE_KEY
        with self.assertRaisesRegex(ReconciliationError, "freeze_authority"):
            self.compare(a, b)

    def test_06_fixed_below_target_consistent_but_no_issuance(self):
        a, b = fake_rpc(1000000), fake_rpc(1000000)
        b["result"]["context"]["slot"] += 5
        out = self.compare(a, b)
        self.assertEqual(out["matching_policy_classification"],
                         "SNAPSHOT_SUGGESTS_IRREVOCABLE_SUPPLY_BELOW_TARGET")
        self.assertFalse(out["sale_or_issuance_authorized"])

    def test_07_active_mint_authority_not_claimed_immutable(self):
        a, b = fake_rpc(mint_authority=OTHER_FAKE_KEY), fake_rpc(mint_authority=OTHER_FAKE_KEY)
        b["result"]["context"]["slot"] += 1
        out = self.compare(a, b)
        self.assertEqual(out["matching_mint_authority"], OTHER_FAKE_KEY)
        self.assertEqual(out["matching_policy_classification"],
                         "AT_TARGET_BUT_MINT_AUTHORITY_STILL_ACTIVE")

    def test_08_stale_slot_difference_rejected(self):
        a, b = two()
        b["result"]["context"]["slot"] = a["result"]["context"]["slot"] + 1501
        with self.assertRaisesRegex(ReconciliationError, "slot gap"):
            self.compare(a, b)

    def test_09_bad_mint_or_program_rejected(self):
        a, b = two()
        b["result"]["value"]["owner"] = "11111111111111111111111111111111"
        with self.assertRaises(ReconciliationError):
            self.compare(a, b)
        a, b = two()
        b["id"] = "wrong"
        with self.assertRaises(ReconciliationError):
            self.compare(a, b)

    def test_10_devnet_mint_cannot_pass(self):
        a, b = two()
        with self.assertRaises(ReconciliationError):
            reconcile("9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw", a, b,
                      "https://api.mainnet-beta.solana.com", "https://another-rpc.example.org")

    def test_11_same_host_rejected(self):
        a, b = two()
        with self.assertRaisesRegex(ReconciliationError, "different claimed RPC"):
            reconcile(FAKE_MINT, a, b, "https://example.org",
                      "https://EXAMPLE.org:443/")

    def test_12_bad_origin_credentials_and_api_key_rejected(self):
        bad = (
            "http://example.org", "https://user:secret@example.org",
            "https://example.org/rpc/private", "https://example.org?api-key=secret",
            "https://localhost", "https://127.0.0.1", "https://example.org:8080",
            "not-a-url",
        )
        for origin in bad:
            with self.subTest(origin=origin), self.assertRaises(ReconciliationError):
                claimed_host(origin)

    def test_13_valid_hostname_normalization(self):
        self.assertEqual(claimed_host("https://RPC.EXAMPLE.ORG:443/"), "rpc.example.org")

    def test_14_missing_authority_key_does_not_mean_revoked(self):
        a, b = two()
        del b["result"]["value"]["data"]["parsed"]["info"]["mintAuthority"]
        with self.assertRaises(ReconciliationError):
            self.compare(a, b)

    def test_15_cli_different_files_and_mismatch_failure(self):
        a, b = two()
        with tempfile.TemporaryDirectory() as d:
            p, q = Path(d) / "first.json", Path(d) / "second.json"
            p.write_text(json.dumps(a), encoding="utf-8")
            q.write_bytes(bytes([0xef, 0xbb, 0xbf]) + json.dumps(b).encode("utf-8"))
            base = ["--mint", FAKE_MINT, "--first-json", str(p),
                    "--second-json", str(q), "--first-origin", "https://first.example.org",
                    "--second-origin", "https://second.example.org"]
            self.assertEqual(main(base), 0)
            self.assertEqual(main(base[:4] + ["--second-json", str(p)] + base[6:]), 2)
            q.write_text(json.dumps(fake_rpc(123)), encoding="utf-8")
            self.assertEqual(main(base), 2)

    def test_16_fake_hostnames_are_not_cryptographic_provenance(self):
        a, b = two()
        out = reconcile(FAKE_MINT, a, b, "https://first.example.org",
                        "https://second.example.org")
        self.assertFalse(out["rpc_provenance_authenticated"])
        self.assertFalse(out["independent_network_sources_proven"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
