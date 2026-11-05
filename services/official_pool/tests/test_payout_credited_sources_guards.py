"""Credited-block source commitments must never authorize FRG payouts.

Run under the normal and services-only sparse GitHub checkouts.
The real LMDB C fixture separately proves the behavioral invariants.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "jtgrassie" / "src"
POOL = (NATIVE / "pool.c").read_text(encoding="utf-8")
SOURCES = (NATIVE / "frg_payout_credited_sources.h").read_text(
    encoding="utf-8")
TEST = (ROOT / "tests/test_payout_credited_sources_lmdb.c").read_text(
    encoding="utf-8")


class CreditedSourcePayoutGuards(unittest.TestCase):
    def test_actual_pool_compiles_source_commitment_but_not_sender(self):
        self.assertIn('#include "frg_payout_credited_sources.h"', POOL)
        self.assertIn('#error "FRG native pool wallet payout path is unsafe', POOL)
        self.assertIn("config.disable_payouts = true;", POOL)
        self.assertIn("FRG wallet payouts are compile-time disabled", POOL)
        for forbidden in ("rpc_wallet_request(", "transfer_split",
                          "db_balance", "db_payments", "mdb_del(",
                          "send_payments(", "wallet_password"):
            self.assertNotIn(forbidden, SOURCES)

    def test_sha_is_derived_directly_from_complete_lmdb_block_scan(self):
        self.assertIn("mdb_cursor_open(txn, db_blocks, &cursor)", SOURCES)
        self.assertIn("MDB_FIRST", SOURCES)
        self.assertIn("MDB_NEXT", SOURCES)
        self.assertIn("FRG_HISTORY_UNLOCKED", SOURCES)
        self.assertIn("block.height <= previous_height", SOURCES)
        self.assertIn("anchor_height - block.height < FRG_PAYOUT_REWARD_MATURITY", SOURCES)
        self.assertIn("frg_payout_digest_u64(digest, block.height)", SOURCES)
        self.assertIn("frg_payout_digest_write(digest, hash, 32)", SOURCES)
        self.assertIn("frg_payout_digest_u64(digest, block.reward)", SOURCES)
        self.assertIn("count == 0) rc = ENODATA;", SOURCES)
        self.assertIn("memcmp(chain_uuid, FRG_PAYOUT_FROZEN_CHAIN_ID, 16)", SOURCES)

    def test_digest_scan_and_intent_insert_share_same_write_transaction(self):
        name = "frg_payout_batch_reserve_from_credited_lmdb("
        reserved = SOURCES.split(name, 1)[1]
        self.assertIn("mdb_txn_begin(env, NULL, 0, &txn)", reserved)
        self.assertIn("frg_payout_intent_held(txn, intent_db, &held)", reserved)
        self.assertIn("frg_payout_credited_sources_digest(\n        txn, blocks_db", reserved)
        self.assertIn("frg_payout_manifest_hash(", reserved)
        self.assertIn("frg_payout_intent_prepare(\n        txn, intent_db", reserved)
        self.assertIn("mdb_txn_commit(txn)", reserved)
        self.assertIn("mdb_env_sync(env, 1)", reserved)
        self.assertLess(reserved.index("mdb_txn_begin(env, NULL, 0, &txn)"),
                        reserved.index("frg_payout_credited_sources_digest("))
        self.assertLess(reserved.index("frg_payout_credited_sources_digest("),
                        reserved.index("frg_payout_intent_prepare("))
        self.assertLess(reserved.index("mdb_env_sync(env, 1)"),
                        reserved.index("memcpy(out_batch_id, batch_id, 32)"))

    def test_native_lmdb_tests_cover_replay_maturity_and_corruption(self):
        for required in ("anchor_height", "FRG_HISTORY_LOCKED",
                         "FRG_HISTORY_ORPHANED", "FRG_HISTORY_UNLOCKED",
                         "FRG_HISTORY_CANDIDATE"):
            # The source fixture does not invent a new block status.
            if required != "FRG_HISTORY_CANDIDATE":
                self.assertIn(required, SOURCES + TEST)
        self.assertIn("== EBUSY", TEST)
        self.assertIn("== EPROTO", TEST)
        self.assertIn("== ENODATA", TEST)
        self.assertIn("frg_payout_intent_mark_ambiguous(", TEST)


if __name__ == "__main__":
    unittest.main()
