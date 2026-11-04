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
        self.assertIn('"--no-initial-sync"', s)
        self.assertIn('"do_not_relay": True', s)
        self.assertIn('"ring_size": 16', s)
        self.assertNotIn('192.168.', s)
        self.assertNotIn('150.136.', s)
        self.assertNotIn('wallet_password, flush=True', s)
        self.assertNotIn('print(tx_hex', s)
        self.assertNotIn('sendrawtransaction', s)

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
