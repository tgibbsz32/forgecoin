#!/usr/bin/env python3
"""Synthetic-only SPL mint initialization provenance parser tests."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_verify_mfrg_mint_snapshot import FAKE_MINT, OTHER_FAKE_KEY, fake_rpc
from verify_mfrg_mint_snapshot import TOKEN_PROGRAM, DEVNET_TEST_MINT
from verify_mfrg_mint_initialization import (
    InitializationError, main, parse_initialization, report, signature_key
)

FAKE_SIG = "1" * 64  # 64 zero bytes. Synthetic, NOT an authentic transaction signature.
SIGNER = OTHER_FAKE_KEY


def tx(*, slot=120000000, kind="initializeMint2", mint=FAKE_MINT,
       decimals=6, mint_authority=SIGNER, freeze_authority=None):
    instruction = {
        "program": "spl-token", "programId": TOKEN_PROGRAM,
        "parsed": {
            "type": kind,
            "info": {
                "mint": mint, "decimals": decimals,
                "mintAuthority": mint_authority,
                "freezeAuthority": freeze_authority
            },
        }
    }
    return {
        "jsonrpc": "2.0", "id": FAKE_SIG,
        "result": {
            "slot": slot, "blockTime": 1700000000, "meta": {
                "err": None, "innerInstructions": None,
            },
            "transaction": {
                "signatures": [FAKE_SIG],
                "message": {
                    "accountKeys": [
                        {"pubkey": SIGNER, "signer": True, "writable": True},
                        {"pubkey": FAKE_MINT, "signer": False, "writable": True},
                        {"pubkey": TOKEN_PROGRAM, "signer": False, "writable": False}
                    ],
                    "instructions": [instruction]
                }
            },
            "version": "legacy"
        }
    }


def compare(first=None, second=None, snapshot=None):
    return report(
        FAKE_MINT, FAKE_SIG, first or tx(), second or tx(),
        snapshot or fake_rpc(), "https://first.example.org",
        "https://second.example.org",
    )


class InitializationEvidenceTests(unittest.TestCase):
    def test_01_two_immutable_parsed_views_are_consistent_but_not_authenticated(self):
        x = compare()
        self.assertTrue(x["offline_parsed_evidence_consistent"])
        self.assertEqual(x["observed_initialization_slot"], 120000000)
        self.assertEqual(x["later_raw_supply_atomic"], "500000000000000")
        self.assertEqual(x["parsed_initialize_instruction"]["instruction_type"], "initializeMint2")
        for key in ("initialized_mint_on_mainnet_authenticated",
                    "independent_rpc_provenance_verified",
                    "transaction_signature_cryptographically_verified",
                    "project_issuer_identity_verified", "mint_and_holder_custody_verified",
                    "founder_or_treasury_tokens_funded", "sale_or_issuance_authorized"):
            self.assertIs(x[key], False, key)

    def test_02_standard_initializeMint_is_recognized(self):
        x = compare(first=tx(kind="initializeMint"), second=tx(kind="initializeMint"))
        self.assertEqual(x["parsed_initialize_instruction"]["instruction_type"], "initializeMint")

    def test_03_inner_cpi_mint_initialize_is_recognized(self):
        a = tx()
        ins = a["result"]["transaction"]["message"]["instructions"].pop()
        a["result"]["meta"]["innerInstructions"] = [{"index": 0, "instructions": [ins]}]
        self.assertEqual(parse_initialization(FAKE_MINT, FAKE_SIG, a)["initialization"]["instruction_type"], "initializeMint2")

    def test_04_failed_tx_is_not_issuance_evidence(self):
        a = tx()
        a["result"]["meta"]["err"] = {"InstructionError": [0, "InvalidArgument"]}
        with self.assertRaisesRegex(InitializationError, "successful"):
            compare(first=a)

    def test_05_wrong_or_missing_init_instruction_rejected(self):
        a = tx(kind="transfer")
        with self.assertRaisesRegex(InitializationError, "Exactly one"):
            compare(first=a)
        a = tx()
        a["result"]["transaction"]["message"]["instructions"] = []
        with self.assertRaises(InitializationError):
            compare(first=a)

    def test_06_wrong_mint_address_within_instruction_rejected(self):
        a = tx(mint=SIGNER)
        with self.assertRaises(InitializationError):
            compare(first=a)

    def test_07_decimals_in_initialize_must_be_six(self):
        a = tx(decimals=9)
        with self.assertRaisesRegex(InitializationError, "wrong decimals"):
            compare(first=a)

    def test_08_wrong_program_is_not_spl_initialize(self):
        a = tx()
        a["result"]["transaction"]["message"]["instructions"][0]["programId"] = SIGNER
        with self.assertRaisesRegex(InitializationError, "Exactly one"):
            compare(first=a)

    def test_09_conflicting_authorities_from_two_views_rejected(self):
        b = tx(mint_authority=FAKE_MINT)
        with self.assertRaisesRegex(InitializationError, "disagree"):
            compare(second=b)

    def test_10_later_current_authority_may_differ_due_to_revocation(self):
        x = compare(snapshot=fake_rpc(mint_authority=None))
        self.assertIsNone(x["later_mint_authority"])
        self.assertEqual(x["parsed_initialize_instruction"]["original_mint_authority"], SIGNER)

    def test_11_bad_signature_and_id_rejected(self):
        for sig in ("garbage", "0" * 64, "1111111", "1" * 65):
            with self.subTest(signature=sig), self.assertRaises(InitializationError):
                signature_key(sig)
        a = tx()
        a["id"] = "unknown"
        with self.assertRaisesRegex(InitializationError, "request id"):
            compare(first=a)

    def test_12_primary_signature_matches_request(self):
        a = tx()
        a["result"]["transaction"]["signatures"] = ["1" * 63]
        with self.assertRaisesRegex(InitializationError, "Primary"):
            compare(first=a)

    def test_13_mint_must_be_writable(self):
        a = tx()
        a["result"]["transaction"]["message"]["accountKeys"][1]["writable"] = False
        with self.assertRaisesRegex(InitializationError, "writable"):
            compare(first=a)

    def test_14_multiple_initializers_for_same_mint_rejected(self):
        a = tx()
        a["result"]["transaction"]["message"]["instructions"].append(copy.deepcopy(
            a["result"]["transaction"]["message"]["instructions"][0]))
        with self.assertRaisesRegex(InitializationError, "Exactly one"):
            compare(first=a)

    def test_15_different_slot_between_sources_rejected(self):
        with self.assertRaisesRegex(InitializationError, "disagree"):
            compare(second=tx(slot=120000001))

    def test_16_creation_slot_cannot_be_after_current_mint_observation(self):
        with self.assertRaisesRegex(InitializationError, "before claimed initialization"):
            compare(first=tx(slot=150000000), second=tx(slot=150000000))

    def test_17_wrong_spl_program_in_mint_snapshot_rejected(self):
        fake = fake_rpc()
        fake["result"]["value"]["owner"] = SIGNER
        with self.assertRaises(InitializationError):
            compare(snapshot=fake)

    def test_18_same_hostname_not_independent_evidence(self):
        with self.assertRaisesRegex(InitializationError, "distinct claimed"):
            report(FAKE_MINT, FAKE_SIG, tx(), tx(), fake_rpc(),
                   "https://first.example.org", "https://FIRST.EXAMPLE.ORG:443")

    def test_19_devnet_mint_fails_closed(self):
        with self.assertRaises(InitializationError):
            report(DEVNET_TEST_MINT, FAKE_SIG, tx(), tx(), fake_rpc(),
                   "https://first.example.org", "https://second.example.org")

    def test_20_missing_getTransaction_response_not_proof_of_absence(self):
        a = tx()
        a["result"] = None
        with self.assertRaisesRegex(InitializationError, "No transaction record"):
            compare(first=a)

    def test_21_cli_handles_windows_bom_and_failure(self):
        with tempfile.TemporaryDirectory(prefix="fake-mfrg-init-") as folder:
            p = Path(folder)
            first, second, mint = p/"one.json", p/"two.json", p/"mint.json"
            first.write_bytes(bytes([239,187,191]) + json.dumps(tx()).encode("utf8"))
            second.write_text(json.dumps(tx()),encoding="utf8")
            mint.write_text(json.dumps(fake_rpc()),encoding="utf8")
            args = ["--mint",FAKE_MINT, "--signature",FAKE_SIG,
                    "--first-transaction",str(first),
                    "--second-transaction",str(second),
                    "--mint-json",str(mint),
                    "--first-origin","https://first.example.org",
                    "--second-origin","https://second.example.org"]
            self.assertEqual(main(args),0)
            second.write_text(json.dumps(tx(slot=9999)),encoding="utf8")
            self.assertEqual(main(args),2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
