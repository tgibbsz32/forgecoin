"""Native payout reservation is a dormant safety module, not a sender.

The real C+LMDB+OpenSSL behavioral integration runs in the CI workflow.
These source tests ensure no payout activation or currency value bypass is
smuggled into otherwise innocuous batch-planning changes.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "jtgrassie" / "src"
POOL = (SOURCE / "pool.c").read_text(encoding="utf-8")
RESERVE = (SOURCE / "frg_payout_batch_reservation.h").read_text(encoding="utf-8")
WORKFLOW = (Path(__file__).resolve().parents[3] /
            ".github/workflows/pool-payout-intent-lmdb-ci.yml").read_text(
                encoding="utf-8")


class PayoutReservationGuards(unittest.TestCase):
    def test_wallet_rpc_and_public_payouts_remain_unconditionally_forbidden(self):
        self.assertIn("#ifdef FRG_TESTED_WALLET_PAYOUTS", POOL)
        self.assertIn('#error "FRG native pool wallet payout path is unsafe', POOL)
        self.assertIn('#include "frg_payout_batch_reservation.h"', POOL)
        self.assertIn("config.disable_payouts = true;", POOL)
        self.assertIn('#ifndef FRG_TESTED_WALLET_PAYOUTS', POOL)
        self.assertIn("FRG wallet payouts are compile-time disabled", POOL)
        self.assertIn("#ifndef FRG_REVIEWED_PUBLIC_POOL", POOL)

    def test_reservation_is_durable_serial_and_replay_blocking(self):
        self.assertIn("memcmp(chain_uuid, FRG_PAYOUT_FROZEN_CHAIN_ID, 16)", RESERVE)
        self.assertIn("MDB_NOSYNC | MDB_NOMETASYNC | MDB_WRITEMAP", RESERVE)
        self.assertIn("frg_payout_manifest_hash(", RESERVE)
        self.assertIn("mdb_txn_begin(env, NULL, 0, &txn)", RESERVE)
        self.assertIn("frg_payout_intent_held(txn, intent_db, &held)", RESERVE)
        self.assertIn("return rc ? rc : EBUSY;", RESERVE)
        self.assertIn("frg_payout_intent_prepare(txn, intent_db", RESERVE)
        self.assertIn("mdb_txn_commit(txn)", RESERVE)
        self.assertIn("mdb_env_sync(env, 1)", RESERVE)
        self.assertIn("frg_payout_intent_read(txn, intent_db", RESERVE)
        self.assertLess(RESERVE.index("mdb_env_sync(env, 1)"),
                        RESERVE.index("memcpy(out_batch_id, batch_id, 32)"))

    def test_no_transfer_settlement_or_balance_debit_in_reservation_module(self):
        for forbidden in ("rpc_wallet_request", "transfer_split",
                          "mdb_del(", "db_balance", "db_payments",
                          "FRG_TESTED_WALLET_PAYOUTS", "send_payments("):
            self.assertNotIn(forbidden, RESERVE)
        self.assertIn("test_payout_batch_reservation_lmdb.c -llmdb -lcrypto",
                      WORKFLOW)


if __name__ == "__main__":
    unittest.main()
