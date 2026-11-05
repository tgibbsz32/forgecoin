"""Pool two-snapshot research check must never become payout authority.

Runs under services-only sparse checkout as well as full repository.
Behavioral proofs execute independently in native C/LMDB CI.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "jtgrassie" / "src"
CROSS = (SRC / "frg_payout_header_crosscheck.h").read_text(encoding="utf-8")
POOL = (SRC / "pool.c").read_text(encoding="utf-8")
TEST = (ROOT / "tests/test_payout_header_crosscheck_lmdb.c").read_text(
    encoding="utf-8")


class HeaderSnapshotCrosscheckGuards(unittest.TestCase):
    def test_pool_payouts_still_build_locked(self):
        self.assertIn('#include "frg_payout_header_crosscheck.h"', POOL)
        self.assertIn('#error "FRG native pool wallet payout path is unsafe', POOL)
        self.assertIn("config.disable_payouts = true;", POOL)
        for forbidden in ("rpc_wallet_request(", "transfer_split",
                          "send_payments(", "db_balance", "db_payments",
                          "FRG_REVIEWED_PUBLIC_POOL", "mdb_del("):
            self.assertNotIn(forbidden, CROSS)

    def test_fail_closed_evidence_must_be_complete_and_tip_must_match(self):
        for required in ('"anchor"', '"credits"',
                         "frg_payout_header_anchor_matches",
                         "frg_payout_anchor_agreement",
                         "observer_a == observer_b",
                         "json_object_array_length(credits_a) != total",
                         "json_object_array_length(credits_b) != total",
                         "FRG_PAYOUT_CROSSCHECK_MAX_CREDITS",
                         "frg_history_compare(a, item.height",
                         "frg_history_compare(b, item.height",
                         "frg_payout_credited_sources_digest("):
            self.assertIn(required, CROSS)
        self.assertIn("return EAGAIN;", CROSS)
        self.assertIn("if (rc) return rc;", CROSS)

    def test_reviewed_snapshot_gate_and_durable_intent_one_transaction(self):
        reservation = CROSS.split(
            "frg_payout_batch_reserve_crosschecked(", 1)[1]
        for required in ("mdb_txn_begin(env, NULL, 0, &txn)",
                         "frg_payout_intent_held(txn, intent_db, &held)",
                         "frg_payout_credited_headers_crosscheck(",
                         "frg_payout_manifest_hash(",
                         "frg_payout_intent_prepare(",
                         "mdb_txn_commit(txn)",
                         "mdb_env_sync(env, 1)",
                         "frg_payout_intent_read(txn, intent_db",
                         "out_batch_id == out_manifest_sha256",
                         "MDB_NOSYNC | MDB_NOMETASYNC | MDB_WRITEMAP"):
            self.assertIn(required, reservation)
        self.assertLess(reservation.index("frg_payout_credited_headers_crosscheck("),
                        reservation.index("frg_payout_intent_prepare("))
        self.assertLess(reservation.index("mdb_env_sync(env, 1)"),
                        reservation.index("memcpy(out_batch_id, batch, 32)"))

    def test_live_ledger_and_missing_witness_tests(self):
        for required in ("== EAGAIN", "== EPROTO", "== EBUSY",
                         "json_object_array_del_idx(",
                         "frg_payout_batch_reserve_crosschecked(",
                         "mdb_env_close(env)", "frg_payout_intent_read(",
                         "FRG_HISTORY_ORPHANED"):
            self.assertIn(required, TEST)


if __name__ == "__main__":
    unittest.main()
