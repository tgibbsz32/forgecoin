"""Offline source/policy guards for disposable native ForgeCoin wallet signing.

This module must never start a wallet, daemon, mine a block or store keys.
"""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import smoke_native_wallet_regtest as sw


class WalletFAKECHAINGuards(unittest.TestCase):
    def test_public_address_rejects_nonaddress_and_binary(self):
        for malformed in (None, 3, b"abcd", "", "a" * 40, "0" * 150):
            with self.subTest(v=str(malformed)[:14]), self.assertRaises(AssertionError):
                sw.must_public_address(malformed)
        self.assertEqual(sw.must_public_address("Y" + "a" * 96), "Y" + "a" * 96)

    def test_script_requires_prelaunch_lock_and_fakechain(self):
        s = (ROOT / "tools/smoke_native_wallet_regtest.py").read_text()
        self.assertIn("require_manifest(manifest)", s)
        self.assertIn('manifest.get("genesis_hash") != FROZEN_GENESIS', s)
        self.assertIn("offline=True", s)
        self.assertIn('TemporaryDirectory(prefix="frg-native-wallet-FAKECHAIN-"', s)
        self.assertIn('"--rpc-bind-ip", "127.0.0.1"', s)
        self.assertIn('"--daemon-address", f"127.0.0.1:{daemon_port}"', s)
        self.assertIn('"--wallet-dir", str(wallet_dir)', s)
        self.assertIn('"--disable-rpc-login"', s)
        self.assertIn('"--no-dns"', s)
        self.assertIn('"--no-initial-sync"', s)
        self.assertIn('"do_not_relay": True', s)
        self.assertIn('"ring_size": 16', s)
        self.assertNotIn('192.168.', s)
        self.assertNotIn('150.136.', s)
        self.assertNotIn('wallet_password, flush=True', s)
        self.assertNotIn('print(tx_hex', s)
        self.assertIn('f"http://127.0.0.1:{port}/{method}"', s)
        self.assertIn('"sendrawtransaction", "get_transaction_pool_hashes"', s)
        self.assertIn('"do_not_relay": True', s)
        self.assertIn('"do_sanity_checks": True', s)
        self.assertIn('state.get("nettype") not in ("fakechain", "regtest")', s)
        self.assertIn('header(daemon_port, 0)["hash"] != FROZEN_GENESIS', s)
        self.assertIn('accepted.get("not_relayed") is not True', s)
        self.assertIn('snapshot.get("tx_hashes")', s)
        self.assertIn('args.validate_mempool', s)
        self.assertIn('args.confirm_transfer', s)
        self.assertIn('args.verify_restart', s)
        self.assertIn('wallet_rpc(receiver_port, "close_wallet")', s)
        self.assertIn('wallet_rpc(receiver_port, "open_wallet"', s)
        self.assertIn('receiver_proc.wait(timeout=10)', s)
        self.assertIn('restored_incoming.get("in") != incoming.get("in")', s)
        self.assertIn('if confirm_transfer and not (validate_mempool and signed_transfer)', s)
        self.assertIn('receiver_args[receiver_args.index("--rpc-bind-port") + 1]', s)
        self.assertIn('wallet_rpc(receiver_port, "get_transfers"', s)
        self.assertIn('call_rpc(daemon_port, "get_block", {"height": wanted_height})', s)

    def test_native_mempool_rpc_rejects_unreviewed_methods(self):
        for method in ("get_info", "stop_daemon", "start_mining",
                       "submitblock", "send_raw_tx"):
            with self.subTest(method=method), self.assertRaises(AssertionError):
                sw.local_daemon_plain_rpc(12345, method, {})

    def test_mempool_testing_cannot_start_without_signature_gate(self):
        from unittest.mock import patch
        with patch.object(sw.os, "name", "posix"):
            with self.assertRaisesRegex(AssertionError, "requires signed"):
                sw.run(Path("/tmp/nonexistent"), Path("/tmp/also-nonexistent"),
                       {}, 120, validate_mempool=True, signed_transfer=False)

    def test_confirmed_transfer_requires_local_mempool_and_signer(self):
        with patch.object(sw.os, "name", "posix"):
            for signed, mempool in ((False, False), (True, False), (False, True)):
                with self.subTest(signed=signed, mempool=mempool):
                    with self.assertRaises(AssertionError):
                        sw.run(Path("/tmp/nonexistent"), Path("/tmp/nonexistent"),
                               {}, 120, signed_transfer=signed,
                               validate_mempool=mempool,
                               confirm_transfer=True)

    def test_restart_never_runs_without_real_confirmed_transfer_gate(self):
        with patch.object(sw.os, "name", "posix"):
            for signed, mempool, confirmed in (
                (False, False, False),
                (True, False, False),
                (True, True, False),
            ):
                with self.subTest(signed=signed, mempool=mempool,
                                  confirmed=confirmed):
                    with self.assertRaisesRegex(AssertionError,
                                                "Recipient restart requires"):
                        sw.run(
                            Path("/tmp/nonexistent"),
                            Path("/tmp/nonexistent"),
                            {}, 120, signed_transfer=signed,
                            validate_mempool=mempool,
                            confirm_transfer=confirmed, verify_restart=True)

    def test_confirmed_receipt_requires_block_and_independent_credit(self):
        txid = "ab" * 32
        good_block = json.dumps({"tx_hashes": [txid]})
        good_incoming = {"in": [{"txid": txid, "amount": 100_000_000}]}
        good_balance = {"balance": 100_000_000, "unlocked_balance": 0}
        sw.assert_confirmed_receipt(good_block, good_incoming, good_balance, txid)
        bad_cases = (
            (json.dumps({"tx_hashes": []}), good_incoming, good_balance),
            (json.dumps({"tx_hashes": [txid, txid]}), good_incoming, good_balance),
            (good_block, {"in": []}, good_balance),
            (good_block, {"in": [{"txid": txid, "amount": 99_999_999}]}, good_balance),
            (good_block, {"in": [{"txid": txid, "amount": 100_000_000},
                                  {"txid": txid, "amount": 100_000_000}]}, good_balance),
            (good_block, good_incoming, {"balance": 0}),
            (good_block, good_incoming, {"balance": True}),
        )
        for block, incoming, balance in bad_cases:
            with self.subTest(block=block[:50], incoming=incoming, balance=balance):
                with self.assertRaises(AssertionError):
                    sw.assert_confirmed_receipt(block, incoming, balance, txid)

    def test_rpc_only_accepts_json_object_with_no_error(self):
        from unittest.mock import MagicMock
        class FakeResponse:
            def __init__(self, payload):
                self.raw = payload.encode()
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def read(self, maximum):
                return self.raw
        with patch.object(sw.urllib.request, "urlopen",
                          return_value=FakeResponse('{"error":null,"result":{"height":81}}')):
            self.assertEqual(sw.wallet_rpc(42000, "get_height"), {"height": 81})
        for payload in ('[]', '{"error":{"code":-1},"result":{}}',
                        '{"result":null}', '{"result":"bad"}'):
            with self.subTest(payload=payload):
                with patch.object(sw.urllib.request, "urlopen",
                                  return_value=FakeResponse(payload)):
                    with self.assertRaises(AssertionError):
                        sw.wallet_rpc(42000, "get_height")

    def test_manifest_is_unchanged_mainnet_locked(self):
        m = json.loads((ROOT / "config/mainnet.identity.json").read_text())
        self.assertIs(m["release_authorized"], False)
        self.assertIs(m["pool"]["payouts_enabled"], False)
        self.assertEqual(m["consensus_guard_stage"], "draft-unbuilt")
        self.assertEqual(m["genesis_hash"], sw.FROZEN_GENESIS)


if __name__ == "__main__":
    unittest.main()
