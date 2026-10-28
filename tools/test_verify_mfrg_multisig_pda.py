#!/usr/bin/env python3
"""Synthetic-only SPL multisig structure / PDA non-attestation tests."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from verify_mfrg_multisig_pda import AuthorityError, assess, main
from test_verify_mfrg_mint_snapshot import FAKE_MINT, fake_rpc, OTHER_FAKE_KEY
from test_reconcile_mfrg_token_accounts import (
    inventory, FIRST_ACCOUNT, SECOND_ACCOUNT, OWNER_A
)
from verify_mfrg_mint_snapshot import TOKEN_PROGRAM, DEVNET_TEST_MINT

SIGNERS = [FAKE_MINT, SECOND_ACCOUNT, TOKEN_PROGRAM, OTHER_FAKE_KEY, DEVNET_TEST_MINT]


def fixture(purpose="operations", threshold=3, amount=50_000_000 * 1_000_000):
    account_list = inventory()
    account_list["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"] = str(amount)
    claim = {
        "purpose": purpose, "authority_type": "spl_multisig",
        "token_account": FIRST_ACCOUNT,
        "owner_authority": OWNER_A,
        "expected_signer_keys": list(SIGNERS),
    }
    manifest = {
        "schema": "mfrg-custody-preflight-v1",
        "network": "mainnet-beta", "mint": FAKE_MINT, "claim": claim,
    }
    authority_response = {
        "id": OWNER_A,
        "result": {
            "context": {"slot": 123456793},
            "value": {
                "owner": TOKEN_PROGRAM, "executable": False,
                "data": {"program": "spl-token", "parsed": {
                    "type": "multisig", "info": {
                        "isInitialized": True,
                        "numRequiredSigners": threshold,
                        "numValidSigners": 5,
                        "signers": list(SIGNERS),
                    }
                }}
            }
        }
    }
    return manifest, fake_rpc(), account_list, authority_response


class MultisigAndPDATests(unittest.TestCase):
    def test_01_regular_3_of_5_structure_matches_but_custody_not_verified(self):
        m, mint, accounts, owner = fixture()
        out = assess(m, mint, accounts, owner)
        self.assertEqual(out["decision"], "OFFLINE_SPL_MULTISIG_STRUCTURE_CONSISTENT_ONLY")
        self.assertEqual(out["num_required_signers"], 3)
        self.assertEqual(out["num_valid_signers"], 5)
        self.assertEqual(out["listed_balance_atomic"], "50000000000000")
        for field in ("rpc_source_authenticated", "mint_creation_authenticated",
                      "inventory_completeness_verified", "beneficial_owner_or_signer_independence_verified",
                      "owner_approved_multisig", "treasury_funded_on_chain_verified",
                      "vesting_contract_audited_or_deployed", "sale_or_issuance_authorized",
                      "signer_control_proven", "signer_policy_approved"):
            self.assertIs(out[field], False, field)

    def test_02_emergency_4_of_5_structure(self):
        m, mint, accounts, owner = fixture("emergency", 4, 1_000_000*1_000_000)
        out = assess(m, mint, accounts, owner)
        self.assertEqual(out["num_required_signers"], 4)
        self.assertEqual(out["purpose"], "emergency")

    def test_03_regular_2_of_5_rejected(self):
        m, mint, accounts, owner = fixture(threshold=2)
        with self.assertRaisesRegex(AuthorityError, "3-of-5"):
            assess(m, mint, accounts, owner)

    def test_04_emergency_3_of_5_rejected(self):
        m, mint, accounts, owner = fixture("emergency", 3, 1000000)
        with self.assertRaisesRegex(AuthorityError, "4-of-5"):
            assess(m, mint, accounts, owner)

    def test_05_signer_mismatch_rejected(self):
        m, mint, accounts, owner = fixture()
        m["claim"]["expected_signer_keys"][0] = "11111111111111111111111111111112"
        with self.assertRaisesRegex(AuthorityError, "signer set conflicts"):
            assess(m, mint, accounts, owner)

    def test_06_duplicate_signer_rejected(self):
        m, mint, accounts, owner = fixture()
        owner["result"]["value"]["data"]["parsed"]["info"]["signers"][0] = SIGNERS[1]
        with self.assertRaisesRegex(AuthorityError, "distinct"):
            assess(m, mint, accounts, owner)

    def test_07_uninitialized_multisig_rejected(self):
        m, mint, accounts, owner = fixture()
        owner["result"]["value"]["data"]["parsed"]["info"]["isInitialized"] = False
        with self.assertRaisesRegex(AuthorityError, "uninitialized"):
            assess(m, mint, accounts, owner)

    def test_08_wrong_multisig_program_rejected(self):
        m, mint, accounts, owner = fixture()
        owner["result"]["value"]["owner"] = FAKE_MINT
        with self.assertRaisesRegex(AuthorityError, "standard SPL"):
            assess(m, mint, accounts, owner)

    def test_09_wrong_account_type_rejected(self):
        m, mint, accounts, owner = fixture()
        owner["result"]["value"]["data"]["parsed"]["type"] = "account"
        with self.assertRaisesRegex(AuthorityError, "not parsed"):
            assess(m, mint, accounts, owner)

    def test_10_token_account_owner_conflict_rejected(self):
        m, mint, accounts, owner = fixture()
        accounts["result"]["value"][0]["account"]["data"]["parsed"]["info"]["owner"] = TOKEN_PROGRAM
        with self.assertRaisesRegex(AuthorityError, "does not match"):
            assess(m, mint, accounts, owner)

    def test_11_token_account_over_budget_rejected(self):
        m, mint, accounts, owner = fixture(amount=100_000_001*1_000_000)
        with self.assertRaisesRegex(AuthorityError, "allocation ceiling"):
            assess(m, mint, accounts, owner)

    def test_12_delegated_and_frozen_escrow_rejected(self):
        for key, value in (("delegate", TOKEN_PROGRAM), ("state", "frozen"),
                           ("closeAuthority", TOKEN_PROGRAM)):
            m, mint, accounts, owner = fixture()
            info = accounts["result"]["value"][0]["account"]["data"]["parsed"]["info"]
            if key == "closeAuthority":
                info[key] = value
            elif key == "delegate":
                info[key] = value
                info["delegatedAmount"] = {"amount": "5", "decimals": 6}
            else:
                info[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(AuthorityError, "separate review"):
                assess(m, mint, accounts, owner)

    def test_13_founder_deferred_cannot_claim_simple_multisig_is_vesting(self):
        m, mint, accounts, owner = fixture("founder_deferred_team_label",3,5_000_000*1_000_000)
        with self.assertRaisesRegex(AuthorityError, "vesting-specific"):
            assess(m, mint, accounts, owner)

    def test_14_program_pda_is_a_blocked_plan_not_an_ed25519_or_multisig_attestation(self):
        m, mint, accounts, owner = fixture("founder_deferred_team_label",3,5_000_000*1_000_000)
        m["claim"]["authority_type"] = "program_pda"
        m["claim"]["program_id"] = TOKEN_PROGRAM
        m["claim"].pop("expected_signer_keys")
        out = assess(m, mint, accounts)
        self.assertEqual(out["decision"], "BLOCKED_REQUIRE_AUTHENTICATED_PDA_DERIVATION_AND_PROGRAM_AUDIT")
        self.assertIs(out["pda_derivation_verified"], False)
        self.assertIs(out["upgrade_authority_verified"], False)
        self.assertIs(out["release_schedule_enforced_on_chain"], False)
        self.assertIs(out["sale_or_issuance_authorized"], False)

    def test_15_pda_with_multisig_snapshot_fails_closed(self):
        m, mint, accounts, owner = fixture()
        m["claim"]["authority_type"] = "program_pda"
        m["claim"]["program_id"] = TOKEN_PROGRAM
        with self.assertRaisesRegex(AuthorityError, "must not"):
            assess(m, mint, accounts, owner)

    def test_16_pda_without_program_id_rejected(self):
        m, mint, accounts, owner = fixture()
        m["claim"]["authority_type"] = "program_pda"
        with self.assertRaises(AuthorityError):
            assess(m, mint, accounts)

    def test_17_stale_authority_snapshot_rejected(self):
        m, mint, accounts, owner = fixture()
        owner["result"]["context"]["slot"] += 1502
        with self.assertRaisesRegex(AuthorityError, "far apart"):
            assess(m, mint, accounts, owner)

    def test_18_historical_devnet_mint_rejected(self):
        m, mint, accounts, owner = fixture()
        m["mint"] = DEVNET_TEST_MINT
        with self.assertRaisesRegex(AuthorityError, "devnet"):
            assess(m, mint, accounts, owner)

    def test_19_incomplete_multisig_signer_counts_rejected(self):
        for field, value in (("numRequiredSigners", "3"), ("numValidSigners", 4),
                             ("numRequiredSigners", True)):
            m, mint, accounts, owner = fixture()
            owner["result"]["value"]["data"]["parsed"]["info"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(AuthorityError):
                assess(m, mint, accounts, owner)

    def test_20_cli_pass_and_fail_on_synthetic_snapshots(self):
        m, mint, accounts, owner = fixture()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            files = {
                "manifest": root/"manifest.json", "mint": root/"mint.json",
                "inventory": root/"inventory.json", "authority": root/"authority.json"
            }
            for key, obj in zip(files, (m,mint,accounts,owner)):
                files[key].write_text(json.dumps(obj), encoding="utf-8")
            argv = [
                "--manifest", str(files["manifest"]), "--mint-json", str(files["mint"]),
                "--inventory-json", str(files["inventory"]), "--authority-json", str(files["authority"])
            ]
            self.assertEqual(main(argv),0)
            files["authority"].write_text(json.dumps({"result": {"value": None}}),encoding="utf-8")
            self.assertEqual(main(argv),2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
