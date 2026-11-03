"""Guardrails for a genuine but isolated native RandomX Stratum test.

No real mining occurs in these tests. Source is checked to guarantee the
integration runner only starts payout-locked localhost FAKECHAIN processes.
"""
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import smoke_native_stratum_regtest as stratum


class NativeStratumOfflineSafety(unittest.TestCase):
    def test_job_validates_native_fields(self):
        job = {"blob": "a1" * 80, "seed_hash": "b2" * 32,
               "job_id": "c3" * 16, "target": "ffffffff", "height": 1}
        response = {"error": None, "result": {"status": "OK",
                    "id": "d4" * 16, "job": job}}
        client_id, found = stratum.check_login(response)
        self.assertEqual(client_id, "d4" * 16)
        self.assertEqual(found, job)
        for key, bad in (("blob", "123"), ("blob", ""), ("seed_hash", "z" * 64),
                         ("job_id", "0" * 31), ("target", "xx" * 4),
                         ("height", 2)):
            modified = {**job, key: bad}
            with self.subTest(key=key, bad=bad), self.assertRaises(AssertionError):
                stratum.check_login({"error": None, "result": {
                    "status": "OK", "id": "d4" * 16, "job": modified,
                }})

    def test_share_generator_has_no_network_or_private_key_api(self):
        source = (ROOT / "services/official_pool/tests/frg_regtest_randomx_share.c").read_text()
        self.assertIn("randomx_calculate_hash(vm, blob, blob_len, hash)", source)
        self.assertIn("#define NONCE_OFFSET 39", source)
        self.assertIn("randomx_init_cache(cache, seed, sizeof(seed))", source)
        for prohibited in ("connect(", "send(", "curl", "wallet-rpc",
                           "RANDOMX_FLAG_FULL_MEM", "stratum_submit", "mainnet.mine"):
            self.assertNotIn(prohibited, source)

    def test_stratum_runtime_requires_locked_manifest_and_loopback(self):
        manifest = json.loads((ROOT / "config/mainnet.identity.json").read_text())
        self.assertGreaterEqual(len(stratum.require_manifest(manifest)), 90)
        source = (ROOT / "tools/smoke_native_stratum_regtest.py").read_text()
        for required in ('socket.create_connection(("127.0.0.1", pool_port)',
                         "offline=True", "test_config(address, pool_dir",
                         "wallet_rpc_absent", '"pool_blocks_found") != 1',
                         '"miner_balance") != 0.0', '"nonce": "wrong"',
                         "Duplicate Stratum share was accepted"):
            with self.subTest(required=required):
                self.assertIn(required, source)
        self.assertNotIn("0.0.0.0", source)
        self.assertNotIn("150.136.209.227", source)
        self.assertNotIn("wallet_transfer(", source)

    def test_stratum_reader_enforces_request_id_and_accepts_job_notification(self):
        class Reader:
            def __init__(self, lines):
                self.lines = iter(x.encode() + b"\n" for x in lines)
            def readline(self, amount):
                return next(self.lines)
        r = Reader([
            '{"jsonrpc":"2.0","method":"job","params":{"height":1}}',
            '{"id":8,"jsonrpc":"2.0","error":null,"result":{"status":"OK"}}',
        ])
        self.assertEqual(stratum.stratum_reply(r, 8)["result"]["status"], "OK")
        with self.assertRaisesRegex(AssertionError, "Unexpected Stratum"):
            stratum.stratum_reply(Reader(['{"id":9,"error":null}']), 8)


if __name__ == "__main__":
    unittest.main()
