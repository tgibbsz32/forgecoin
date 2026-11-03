"""Source-only guardrails for genuine native C-pool / FAKECHAIN smoke.
Tests never launch a daemon, pool, signer, Stratum, or wallet.
"""
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import smoke_native_pool_regtest as pool_smoke


class PrivatePoolSmokeSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "config/mainnet.identity.json").read_text(encoding="utf-8"))

    def test_manifest_must_be_prelaunch_locked(self):
        address = pool_smoke.require_manifest(self.manifest)
        self.assertGreaterEqual(len(address), 90)
        for section, name, value in (
            ("", "release_authorized", True),
            ("", "mined_blocks_permitted_before_launch", 1),
            ("", "consensus_guard_stage", "approved"),
            ("pool", "payouts_enabled", True),
            ("pool", "stratum_public", True),
            ("pool", "operator_fee_fraction", "0.03"),
            ("ports", "daemon_rpc", 19481),
        ):
            with self.subTest(field=name):
                bad = json.loads(json.dumps(self.manifest))
                if section:
                    bad[section][name] = value
                else:
                    bad[name] = value
                with self.assertRaises(AssertionError):
                    pool_smoke.require_manifest(bad)

    def test_confined_native_pool_config_has_no_wallet_keys(self):
        address = pool_smoke.require_manifest(self.manifest)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pool").mkdir()
            config = pool_smoke.test_config(
                address, root / "pool", 4250, 4251, 4252).read_text()
        expected = (
            "pool-listen = 127.0.0.1",
            "webui-listen = 127.0.0.1",
            "rpc-host = 127.0.0.1",
            "rpc-port = 39481",
            "wallet-rpc-host = 127.0.0.1",
            "wallet-rpc-port = 4252",
            "pool-wallet = " + address,
            "pool-fee = 0.01",
            "disable-payouts = 1",
            "disable-self-select = 1",
            "disable-hash-check = 0",
            "forked = 0",
            "processes = 1",
            "pool-view-key = " + "0" * 64,
        )
        for text in expected:
            with self.subTest(config_line=text):
                self.assertIn(text + "\n", config)
        self.assertIn("pool-fee-wallet = \n", config)
        self.assertNotIn("0.0.0.0", config)

    def test_source_never_starts_wallet_or_production_miner(self):
        source = (ROOT / "tools/smoke_native_pool_regtest.py").read_text()
        self.assertIn('from smoke_regtest_reorg import (', source)
        self.assertIn("offline=True", source)
        self.assertIn("wallet-rpc-port", source)
        self.assertIn("str(k) for k in []" if False else "pool-view-key", source)
        self.assertIn('if k != "MONERO_RANDOMX_FULL_MEM"', source)
        self.assertIn('f"http://127.0.0.1:{port}/stats"', source)
        self.assertIn('os.kill(pool.pid, signal.SIGUSR1)', source)
        self.assertNotIn("150.136.209.227", source)
        self.assertNotIn("http://0.0.0.0", source)
        self.assertNotIn("wallet_transfer(", source)


if __name__ == "__main__":
    unittest.main()
