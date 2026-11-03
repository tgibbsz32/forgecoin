"""Offline fork provenance, monetary semantics and safe-default assertions.

These are static compatibility tests, NOT proof that the C pool compiles or
produces a valid accepted block. Never make network/daemon/wallet calls.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
VENDOR = Path(__file__).resolve().parents[1] / "jtgrassie"


class NativeBackendPreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool = (VENDOR / "src/pool.c").read_text(encoding="utf-8")
        cls.webui = (VENDOR / "src/webui.c").read_text(encoding="utf-8")
        cls.conf = dict(line.split("=", 1) for line in [
            x.strip() for x in (VENDOR / "pool.conf").read_text(encoding="utf-8").splitlines()
        ] if "=" in line and not line.startswith("#"))
        cls.conf = {k.strip(): v.strip() for k, v in cls.conf.items()}
        cls.currency = (VENDOR / "src/frg_currency.h").read_text(encoding="utf-8")
        cls.chain = (ROOT / "src/cryptonote_config.h").read_text(encoding="utf-8")

    def test_graceful_shutdown_is_in_libevent_thread_and_webui_is_not_detached(self):
        self.assertIn("signal_sigint = evsignal_new(pool_base, SIGINT", self.pool)
        self.assertIn("signal_sigterm = evsignal_new(pool_base, SIGTERM", self.pool)
        self.assertIn("event_base_loopexit(pool_base, NULL);", self.pool)
        self.assertNotIn("sigint_handler(int sig)", self.pool)
        self.assertNotIn("signal(SIGTERM, sigint_handler)", self.pool)
        self.assertIn("run(&uic);", self.pool)
        self.assertIn("start_web_ui(web_context, pool_base)", self.pool)
        self.assertIn("evhttp_new(base)", self.webui)
        self.assertIn("evhttp_bind_socket_with_handle(webui_httpd", self.webui)
        self.assertIn("evhttp_free(webui_httpd)", self.webui)
        self.assertNotIn("pthread_detach", self.webui)
        self.assertNotIn("event_base_dispatch(webui_base)", self.webui)
        self.assertNotIn("event_base_free(webui_base)", self.webui)

    def test_frg_currency_matches_checkout_consensus(self):
        self.assertRegex(self.chain, r"#define COIN\s+\(\(uint64_t\)100000000\)")
        self.assertRegex(self.chain, r"#define CRYPTONOTE_DISPLAY_DECIMAL_POINT\s+8")
        self.assertIn("FRG_ATOMIC_UNITS UINT64_C(100000000)", self.currency)
        self.assertIn("FRG_COIN_DECIMALS 8", self.currency)
        # Public main still carries the retired native prefix 90. Its C pool
        # must FAIL CLOSED until frozen consensus PR #185 (190) is reviewed;
        # do not require unrelated consensus changes in a pool-only PR.
        prefix = re.search(
            r"CRYPTONOTE_PUBLIC_ADDRESS_BASE58_PREFIX\\s*=\\s*(90|190);",
            self.chain,
        )
        self.assertIsNotNone(prefix)
        if prefix.group(1) == "90":
            self.assertIn("!frg_matches_frozen_mainnet()", self.pool)
        self.assertIn("#define MAINNET_ADDRESS_PREFIX 190", self.pool)
        self.assertIn("#define BLOCK_TIME 120", self.pool)

    def test_backend_payout_threshold_never_uses_float_units(self):
        self.assertIn("frg_parse_amount_atomic(val, &config.payment_threshold_atomic)", self.pool)
        self.assertIn("uint64_t threshold = config.payment_threshold_atomic;", self.pool)
        self.assertNotIn("1000000000000", self.pool)
        self.assertIn("frg_pool_fee_atomic(amount)", self.pool)
        self.assertIn("return amount / UINT64_C(100);", self.currency)
        self.assertNotIn("amount * config.pool_fee", self.pool)

    def test_complete_credited_history_audit_is_fail_closed(self):
        """Historical validation supplements, not replaces, recent 10-header maturity checks."""
        self.assertIn('#include "frg_credited_history_audit.h"', self.pool)
        self.assertIn('#include "frg_credited_ledger_scan.h"', self.pool)
        self.assertIn("frg_history_scan_credited(", self.pool)
        self.assertIn("get_block_header_by_height", self.pool)
        self.assertIn("rpc_on_frq_historical_credit", self.pool)
        self.assertIn("FRG_HISTORY_CONFLICT", self.pool)
        self.assertIn("frg_quarantine_mark(env, db_properties, expected->stored.height)", self.pool)
        self.assertIn("frg_history_sweep_verified = false;", self.pool)
        self.assertIn("frg_history_epoch++;", self.pool)
        self.assertIn("frg_history_payout_allowed(frg_accounting_held,", self.pool)
        self.assertIn("timer_on_history", self.pool)
        self.assertIn("frg_history_requested_at", self.pool)
        self.assertIn("frg_history_request_sequence", self.pool)
        self.assertIn("frg_history_unverified", self.pool)
        self.assertIn("#ifndef FRG_TESTED_WALLET_PAYOUTS", self.pool)
        self.assertIn("#ifndef FRG_REVIEWED_PUBLIC_POOL", self.pool)
        scan = (VENDOR / "src/frg_credited_ledger_scan.h").read_text(encoding="utf-8")
        self.assertIn("MDB_NEXT", scan)  # includes DUPFIXED blocks sharing a height
        self.assertIn("value.mv_size != sizeof(frg_history_saved_t)", scan)
        self.assertIn("item.height != key_height", scan)
        self.assertIn("item.status != FRG_HISTORY_UNLOCKED", scan)
        self.assertIn("return rc == MDB_NOTFOUND ? 0 : rc;", scan)

    def test_native_maturity_policy_is_wired_at_both_unlock_paths(self):
        self.assertIn('#include "frg_reward_maturity.h"', self.pool)
        self.assertIn("frg_reward_mature(block->height, height)", self.pool)
        self.assertIn("frg_mature_header_window(", self.pool)
        # Overflow-safe subtraction is mandatory; the old sum could wrap.
        self.assertNotIn("block->height + 60 > height", self.pool)
        self.assertNotIn("top->height - 60;", self.pool)
        header = (VENDOR / "src/frg_reward_maturity.h").read_text(encoding="utf-8")
        self.assertIn("FRG_MINED_REWARD_UNLOCK_WINDOW UINT64_C(60)", header)
        self.assertIn("tip_height - block_height", header)
        self.assertIn("last < count - UINT64_C(1)", header)

    def test_native_pplns_cannot_lose_fees_or_unlock_partial_rewards(self):
        self.assertIn('#include "frg_pplns_accounting.h"', self.pool)
        allocation = self.pool.split("payout_block(block_t *block, MDB_txn *parent)", 1)[1].split(
            "static int\nprocess_blocks(", 1
        )[0]
        self.assertIn("if (!config.pool_fee_wallet[0])", allocation)
        self.assertIn("frg_pplns_share_atomic(", allocation)
        self.assertIn("frg_pool_fee_atomic(amount)", allocation)
        self.assertIn('Fee ledger credit failed; aborting full allocation', allocation)
        self.assertIn("mdb_txn_abort(txn);\n                return rc;", allocation)
        self.assertIn("frg_pplns_fully_accounted(block->reward, total_paid)", allocation)
        self.assertIn("return EPROTO;", allocation)
        self.assertNotIn("total_paid + amount", allocation)
        self.assertNotIn("floor((double)share->difficulty", allocation)
        self.assertNotIn("if (fee > 0 && config.pool_fee_wallet[0])", allocation)
        helper = (VENDOR / "src/frg_pplns_accounting.h").read_text(encoding="utf-8")
        self.assertIn("block_reward - credited_so_far", helper)
        self.assertIn("proposed >= (long double)remaining", helper)
        self.assertIn("block_reward != UINT64_C(0)", helper)

    def test_all_block_status_updates_are_atomic_with_balances(self):
        reconciliation = self.pool.split("static int\nprocess_blocks(", 1)[1].split(
            "static void\nupdate_pool_hr(", 1
        )[0]
        self.assertEqual(
            reconciliation.count(
                "if ((rc = mdb_cursor_put(cursor, &key, &new_val, MDB_CURRENT)))"
            ), 4,
        )
        self.assertNotIn(
            "                mdb_cursor_put(cursor, &key, &new_val, MDB_CURRENT);",
            reconciliation,
        )
        self.assertEqual(
            reconciliation.count("Block status ledger write failed; aborting all credits"),
            4,
        )
        self.assertEqual(reconciliation.count("mdb_txn_abort(txn);"), 8)
        self.assertIn("return rc;", reconciliation)
        self.assertIn("aborting canonical reconciliation batch", reconciliation)

    def test_canonical_header_range_requires_complete_anchored_response(self):
        self.assertIn('#include "frg_canonical_headers.h"', self.pool)
        callback = self.pool.split(
            "rpc_on_block_headers_range(const char* data, rpc_callback_t *callback)", 1
        )[1].split("static void\nrpc_on_block_template(", 1)[0]
        self.assertIn("frg_canonical_headers_valid(headers, expected->start", callback)
        self.assertIn("Incomplete, inconsistent or stale canonical header range", callback)
        self.assertIn("block_t verified[BLOCK_HEADERS_RANGE] = {0};", callback)
        self.assertIn("process_blocks(verified, headers_len, expected->tip_height)", callback)
        self.assertIn("#if BLOCK_HEADERS_RANGE != FRG_CANONICAL_HEADERS_MAX", self.pool)
        self.assertIn("if (process_blocks(verified, headers_len, expected->tip_height))", callback)
        self.assertNotIn("process_blocks(block_headers_range, BLOCK_HEADERS_RANGE)", callback)
        self.assertNotIn("block_headers_range[i]", callback)
        self.assertIn("if (!expected ||", callback)
        schedule = self.pool.split("frg_mature_header_window(", 1)[1].split(
            "json_object_put(root);", 1
        )[0]
        self.assertIn("expected->start = start", schedule)
        self.assertIn("expected->end = end", schedule)
        self.assertIn("expected->tip_height = top->height", schedule)
        self.assertIn("rpc_on_block_headers_range, expected, 0", schedule)
        header = (VENDOR / "src/frg_canonical_headers.h").read_text(encoding="utf-8")
        self.assertIn("FRG_CANONICAL_HEADERS_MAX 10", header)
        self.assertIn("json_object_array_length(", header)
        self.assertIn("strcmp(parent, prior_hash)", header)
        self.assertIn("requested_start + (uint64_t)i", header)

    def test_native_reorg_freezes_credited_blocks_and_checks_tip_maturity(self):
        self.assertIn('#include "frg_reconcile_policy.h"', self.pool)
        self.assertIn("(int)BLOCK_UNLOCKED == (int)FRG_SAVED_UNLOCKED", self.pool)
        core = self.pool.split("static int\nprocess_blocks(", 1)[1].split(
            "static void\nupdate_pool_hr(", 1
        )[0]
        self.assertIn("frg_reconcile_block(", core)
        self.assertIn("sb->status, sb->height, ib->height, observed_tip_height", core)
        self.assertIn("FRG_RECONCILE_ABORT_DEEP_REORG", core)
        self.assertIn("abort this accounting batch; manual review required", core)
        self.assertIn("return EPROTO;", core)
        self.assertIn("FRG_RECONCILE_DEFER", core)
        self.assertIn("FRG_RECONCILE_ALREADY_CREDITED", core)
        self.assertIn("FRG_RECONCILE_ALREADY_ORPHANED", core)
        self.assertNotIn("if (sb->status != BLOCK_LOCKED)\n                continue", core)
        self.assertIn("observed_tip_height", core)
        startup = self.pool.split("rpc_on_block_header_by_height(", 1)[1].split(
            "static void\nrpc_on_block_headers_range(", 1
        )[0]
        self.assertIn("process_blocks(&rb, 1, pool_stats.network_height)", startup)
        helper = (VENDOR / "src/frg_reconcile_policy.h").read_text(encoding="utf-8")
        self.assertIn("frg_reward_mature(saved_height, tip_height)", helper)
        self.assertIn("FRG_RECONCILE_ABORT_DEEP_REORG", helper)
        self.assertIn("FRG_RECONCILE_MARK_ORPHAN", helper)

    def test_deep_reorg_quarantine_persists_and_blocks_restart_and_payments(self):
        self.assertIn('#include "frg_accounting_quarantine.h"', self.pool)
        self.assertIn("static bool frg_accounting_held;", self.pool)
        initialize = self.pool.split("static int\ndatabase_init(", 1)[1].split(
            "static void\ndatabase_close(", 1
        )[0]
        self.assertIn("frg_quarantine_read(audit, db_properties, &held, NULL)", initialize)
        self.assertIn("return rc ? rc : EACCES;", initialize)
        core = self.pool.split("static int\nprocess_blocks(", 1)[1].split(
            "static void\nupdate_pool_hr(", 1
        )[0]
        self.assertIn("frg_quarantine_read(txn, db_properties, &held, NULL)", core)
        self.assertIn("frg_accounting_held = true;", core)
        self.assertIn("frg_quarantine_mark(", core)
        self.assertIn("exit(EXIT_FAILURE);", core)
        hold = core.split("const uint64_t conflict_height = sb->height;", 1)[1]
        self.assertLess(hold.index("mdb_txn_abort(txn);"), hold.index(
            "frg_quarantine_mark("
        ))
        send = self.pool.split("static int\nsend_payments(void)", 1)[1].split(
            "static ", 1
        )[0]
        self.assertIn("frg_quarantine_read(hold_txn, db_properties, &held, NULL)", send)
        self.assertIn("payouts blocked by durable reorganization quarantine", send)
        header = (VENDOR / "src/frg_accounting_quarantine.h").read_text(encoding="utf-8")
        self.assertIn("FRG_QUARANTINE_PROPERTY", header)
        self.assertIn("MDB_BAD_VALSIZE", header)
        self.assertIn("MDB_NOOVERWRITE", header)
        self.assertNotIn("frg_quarantine_clear(", header)

    def test_balance_add_must_abort_on_write_failure_or_uint64_overflow(self):
        ledger = self.pool.split("static int\nbalance_add(", 1)[1].split(
            "static int\npayout_block(", 1
        )[0]
        self.assertIn("frg_balance_credit_safe(", ledger)
        self.assertIn("if (val.mv_size != sizeof(uint64_t))", ledger)
        self.assertIn("return MDB_BAD_VALSIZE;", ledger)
        self.assertIn("return EOVERFLOW;", ledger)
        self.assertIn("Failed to create miner/fee balance", ledger)
        self.assertIn("Failed to update miner/fee balance", ledger)
        self.assertGreaterEqual(ledger.count("mdb_txn_abort(txn);"), 5)
        self.assertNotIn("current_amount += amount;", ledger)
        helper = (VENDOR / "src/frg_pplns_accounting.h").read_text(encoding="utf-8")
        self.assertIn("increment > UINT64_MAX - existing", helper)

    def test_miner_balance_uses_8_decimal_integer_json(self):
        self.assertIn('mb / FRG_ATOMIC_UNITS, mb % FRG_ATOMIC_UNITS', self.webui)
        self.assertIn('mb = balance;', self.webui)
        self.assertNotIn("1000000000000.0", self.webui)
        self.assertNotIn('"miner_balance\\":%.8f', self.webui)

    def test_configuration_safe_defaults(self):
        want = {
            "pool-listen": "127.0.0.1",
            "webui-listen": "127.0.0.1",
            "rpc-host": "127.0.0.1",
            "rpc-port": "39481",
            "wallet-rpc-host": "127.0.0.1",
            "wallet-rpc-port": "0",
            "disable-payouts": "1",
            "disable-hash-check": "0",
            "disable-self-select": "1",
            "pool-fee": "0.01",
            "payment-threshold": "0.33",
            "pool-wallet": "",
        }
        for key, expected in want.items():
            with self.subTest(key=key):
                self.assertEqual(self.conf.get(key), expected)
        self.assertNotIn("9y4V6rSRb", (VENDOR / "pool.conf").read_text(encoding="utf-8"))

    def test_failed_wallet_payouts_are_not_debited(self):
        self.assertIn("Malformed wallet payout response; balances unchanged", self.pool)
        self.assertIn("Wallet payout failed or ambiguous; no balance debits", self.pool)
        self.assertIn('"tx_hash_list"', self.pool)
        self.assertIn("No transaction-hash evidence in wallet response", self.pool)
        self.assertIn("json_object_array_length(hashes) == 0", self.pool)

    def test_frozen_mainnet_runtime_identity_gate(self):
        xmr = (VENDOR / "src/xmr.cpp").read_text(encoding="utf-8")
        self.assertIn("frg_matches_frozen_mainnet", xmr)
        self.assertIn("!frg_matches_frozen_mainnet()", self.pool)
        self.assertIn("config.rpc_port != 39481", self.pool)
        for value in ("== 190", "== 191", "== 192", "== 39480", "== 39481", "== 39482"):
            self.assertIn(value, xmr)
        # Old consensus is NOT secretly treated as the new chain.
        # Public main still carries the retired native prefix 90. Its C pool
        # must FAIL CLOSED until frozen consensus PR #185 (190) is reviewed;
        # do not require unrelated consensus changes in a pool-only PR.
        prefix = re.search(
            r"CRYPTONOTE_PUBLIC_ADDRESS_BASE58_PREFIX\\s*=\\s*(90|190);",
            self.chain,
        )
        self.assertIsNotNone(prefix)
        if prefix.group(1) == "90":
            self.assertIn("!frg_matches_frozen_mainnet()", self.pool)

    def test_fail_closed_share_block_and_wallet_paths(self):
        self.assertIn("nonce must be exactly 8 hex characters", self.pool)
        self.assertIn("Rejected low-difficulty shares must not inflate", self.pool)
        self.assertIn("Block submission unconfirmed", self.pool)
        self.assertIn("Malformed wallet payout response; balances unchanged", self.pool)
        self.assertIn("Wallet payout failed or ambiguous; no balance debits", self.pool)
        self.assertIn('"tx_hash_list"', self.pool)
        self.assertIn("No transaction-hash evidence in wallet response", self.pool)

    def test_daemon_block_submission_must_persist_before_reporting(self):
        callback = self.pool.split(
            "rpc_on_block_submitted(const char* data, rpc_callback_t *callback)", 1
        )[1].split("rpc_on_wallet_transferred(", 1)[0]
        self.assertIn('#include "frg_block_submit_receipt.h"', self.pool)
        self.assertIn("frg_block_submission_rpc_accepted(root)", callback)
        self.assertIn('data ? json_tokener_parse(data) : NULL', callback)
        self.assertIn('callback ? (block_t*)callback->data : NULL', callback)
        self.assertLess(
            callback.index("if (!frg_block_submission_rpc_accepted(root))"),
            callback.index("store_block(b->height, b)"),
        )
        self.assertLess(
            callback.index("if (!b)"), callback.index("store_block(b->height, b)")
        )
        self.assertLess(
            callback.index("store_block(b->height, b)"),
            callback.index("pool_stats.pool_blocks_found++"),
        )
        self.assertIn("if (rc)", callback)
        self.assertLess(
            callback.index("if (rc)"),
            callback.index("pool_stats.pool_blocks_found++"),
        )
        self.assertIn("canonical confirmation remains pending", callback)
        self.assertNotIn("payout_block(", callback)
        self.assertNotIn("balance_add(", callback)

    def test_share_credit_follows_durable_storage(self):
        start = self.pool.index("    if (can_store)")
        end = self.pool.index("    if (retarget_required(client, job))", start)
        body = self.pool[start:end]
        self.assertLess(body.index("store_share(share.height, &share)"),
                        body.index("client->hashes += job->target"))
        self.assertLess(body.index("store_share(share.height, &share)"),
                        body.index('stratum_get_status_body(body, client->json_id, "OK")'))
        self.assertIn("pthread_rwlock_wrlock(&rwlock_acc)", body)
        self.assertIn('share storage unavailable', body)

    def test_runtime_rejects_unsafe_user_configs(self):
        self.assertIn("#ifndef FRG_REVIEWED_PUBLIC_POOL", self.pool)
        self.assertIn('strcmp(config.pool_listen, "127.0.0.1")', self.pool)
        self.assertIn('strcmp(config.webui_listen, "127.0.0.1")', self.pool)
        self.assertIn("config.disable_hash_check || !config.disable_payouts", self.pool)
        self.assertIn("!config.disable_self_select", self.pool)
        self.assertIn("#ifndef FRG_TESTED_WALLET_PAYOUTS", self.pool)
        self.assertIn("FRG wallet payouts are compile-time disabled", self.pool)

    def test_upstream_license_and_pinned_build_contract(self):
        lic = (VENDOR / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2018, The Monero Project", lic)
        self.assertIn("Redistribution and use in source and binary forms", lic)
        make = (VENDOR / "Makefile").read_text(encoding="utf-8")
        self.assertIn("TARGET = forgecoin-pool", make)
        self.assertIn("FORGECOIN_ROOT", make)
        self.assertIn("MONERO_ROOT := $(FORGECOIN_ROOT)", make)


if __name__ == "__main__":
    unittest.main()
