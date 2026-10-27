"""Prelaunch payout guard contract checks; complements compiled C fixtures.

These never authorize wallet RPC spending: a chain-confirmed payout and crash
recovery still need production-key-free integration testing.
"""
import pathlib
import re
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=(ROOT/"jtgrassie/src/pool.c").read_text(encoding="utf-8")
HEADER=(ROOT/"jtgrassie/src/frg_transfer_receipt.h").read_text(encoding="utf-8")

class PayoutSafetyContracts(unittest.TestCase):
    def test_wallet_rpc_failure_before_any_balance_updates(self):
        fn=SRC.split("rpc_on_wallet_transferred(const char* data, rpc_callback_t *callback)",1)[1].split("static int\nsend_payments",1)[0]
        self.assertLess(fn.index("if (!frg_transfer_receipt_valid(root))"),fn.index("db_balance"))
        self.assertIn('retaining all miner balances',fn)
        self.assertNotIn('log_trace("Transfer response',fn)

    def test_ledger_record_and_balance_are_atomic(self):
        fn=SRC.split("rpc_on_wallet_transferred(const char* data, rpc_callback_t *callback)",1)[1].split("static int\nsend_payments",1)[0]
        self.assertEqual(fn.count("mdb_txn_commit(txn)"),1)
        self.assertEqual(fn.count("pdb_txn_begin(env"),1)
        self.assertLess(fn.index("db_balance"),fn.index("db_payments"))
        self.assertLess(fn.index("db_payments"),fn.index("mdb_txn_commit(txn)"))
        self.assertIn("Payment exceeded available miner balance; ledger transaction rejected",fn)

    def test_native_pplns_never_unlocks_incomplete_reward(self):
        fn=SRC.split("payout_block(block_t *block, MDB_txn *parent)",1)[1].split("static int\nprocess_blocks",1)[0]
        self.assertIn("frg_pplns_share_reward_atomic(",fn)
        self.assertNotIn("floor((double)",fn)
        self.assertIn("if (total_paid != block->reward)",fn)
        self.assertIn("return MDB_NOTFOUND;",fn)
        self.assertIn("mdb_txn_abort(txn);",fn)

    def test_balance_credit_never_commits_failed_write_or_wraps(self):
        fn=SRC.split("balance_add(const char *address, uint64_t amount, MDB_txn *parent)",1)[1].split("static int\npayout_block",1)[0]
        self.assertIn("frg_checked_balance_add(current_amount, amount, &updated_amount)",fn)
        self.assertIn("Refusing miner balance overflow",fn)
        self.assertIn("Balance insert rejected:",fn)
        self.assertIn("Balance update rejected:",fn)
        self.assertEqual(fn.count("mdb_txn_commit(txn)"),1)
        self.assertGreaterEqual(fn.count("mdb_txn_abort(txn)"),4)
        self.assertEqual(fn.count("mdb_cursor_close(cursor)"),5)

    def test_mature_block_state_and_balances_commit_atomically(self):
        fn=SRC.split("process_blocks(block_t *blocks, size_t count)",1)[1].split("static void\nupdate_pool_hr",1)[0]
        self.assertIn("goto rollback_block_ledger;",fn)
        self.assertEqual(fn.count("mdb_txn_commit(txn)"),1)
        self.assertEqual(fn.count("mdb_txn_abort(txn)"),2)
        self.assertIn("Failed to mark hash-mismatched orphan",fn)
        self.assertIn("Failed to mark parent-mismatched orphan",fn)
        self.assertIn("Failed to mark daemon-reported orphan",fn)
        self.assertIn("if ((rc = mdb_cursor_put(cursor, &key, &new_val, MDB_CURRENT)))",fn)
        self.assertIn("if (rc)\n                {\n                    log_error(\"Refusing partial mature block ledger credit",fn)
        self.assertLess(fn.index("rc = payout_block(&nb, txn)"),
                        fn.index("Mature block credited in local ledger"))
        self.assertIn("rollback_block_ledger:\n    mdb_cursor_close(cursor);\n    mdb_txn_abort(txn);",fn)

    def test_unsafe_wallet_spending_cannot_be_enabled_with_macro(self):
        self.assertIn("#if defined(FRG_TESTED_WALLET_PAYOUTS)",SRC)
        self.assertIn('#error "Unsafe FRG pool wallet payouts prohibited:',SRC)
        self.assertIn('log_debug("Prepared private wallet payout batch',SRC)
        self.assertNotIn("log_trace(body);",SRC)

    def test_wallet_rpc_receipt_not_yet_on_chain_confirmed(self):
        fn=SRC.split("rpc_on_wallet_transferred(const char* data, rpc_callback_t *callback)",1)[1].split("static int\nsend_payments",1)[0]
        self.assertIn("confirmation still pending",fn)
        self.assertNotIn("get_transfers",fn)
        self.assertNotIn("get_transfer_by_txid",fn)
        self.assertIn("#ifndef FRG_TESTED_WALLET_PAYOUTS",SRC)
        # This test documents why public payout authorization stays false.
        # A response TXID does NOT prove confirmed, matched, idempotent payment.

    def test_next_block_statistics_use_actual_mining_template(self):
        template = SRC.split("rpc_on_block_template(const char* data, rpc_callback_t *callback)",1)[1].split("static int\nstartup_scan_round_shares",1)[0]
        header = SRC.split("rpc_on_last_block_header(const char* data, rpc_callback_t *callback)",1)[1].split("static void\nrpc_on_block_submitted",1)[0]
        self.assertIn("pool_stats.network_difficulty = cand.difficulty;",template)
        self.assertIn("pool_stats.network_height = cand.height;",template)
        self.assertNotIn("pool_stats.network_difficulty = top->difficulty;",header)

    def test_mainnet_payout_guard_still_disabled(self):
        self.assertIn("#ifndef FRG_TESTED_WALLET_PAYOUTS",SRC)
        self.assertIn('config.disable_hash_check || !config.disable_payouts',SRC)
        self.assertIn('config.share_mul != 2.0',SRC)

    def test_receipt_requires_valid_nonempty_tx_list(self):
        self.assertIn('"tx_hash_list"',HEADER)
        self.assertIn("if (count==0 || count>128) return 0;",HEADER)

if __name__=="__main__": unittest.main()
