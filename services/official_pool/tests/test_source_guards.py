"""Offline fork provenance, monetary semantics and safe-default assertions.

These are static compatibility tests, NOT proof that the C pool compiles or
produces a valid accepted block. Never make network/daemon/wallet calls.
"""
from pathlib import Path
import json
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

    def test_frg_currency_matches_checkout_consensus(self):
        self.assertRegex(self.chain, r"#define COIN\s+\(\(uint64_t\)100000000\)")
        self.assertRegex(self.chain, r"#define CRYPTONOTE_DISPLAY_DECIMAL_POINT\s+8")
        self.assertIn("FRG_ATOMIC_UNITS UINT64_C(100000000)", self.currency)
        self.assertIn("FRG_COIN_DECIMALS 8", self.currency)
        self.assertRegex(self.chain, r"CRYPTONOTE_PUBLIC_ADDRESS_BASE58_PREFIX\s*=\s*190;")
        self.assertIn("#define MAINNET_ADDRESS_PREFIX 190", self.pool)
        self.assertIn("#define BLOCK_TIME 120", self.pool)

    def test_backend_payout_threshold_never_uses_float_units(self):
        self.assertIn("frg_parse_amount_atomic(val, &config.payment_threshold_atomic)", self.pool)
        self.assertIn("uint64_t threshold = config.payment_threshold_atomic;", self.pool)
        self.assertNotIn("1000000000000", self.pool)
        self.assertIn("frg_pool_fee_atomic(amount)", self.pool)
        self.assertIn("return amount / UINT64_C(100);", self.currency)
        self.assertNotIn("amount * config.pool_fee", self.pool)

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

    def test_official_fee_treasury_matches_mainnet_manifest_and_preserves_prelaunch_safety(self):
        manifest = json.loads((ROOT / "config/mainnet.identity.json").read_text(encoding="utf-8"))
        public_address = manifest["pool"]["operator_fee_address"]
        self.assertEqual(public_address,
                         "YnJPKnrv2fk6MdHkvvAxDbe1L3Dv7WgtrjPBHnP3NokU1Zri6a8da9SfoDiF9SpQxP4Xn18BT2bBNLnVtCPqXTvr1UTsca4Z4")
        self.assertEqual(self.conf["pool-fee-wallet"], public_address)
        self.assertRegex(public_address, r"^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{97}$")
        self.assertIn("valid standard mainnet", manifest["pool"]["operator_fee_address_validation"])
        self.assertEqual(manifest["pool"]["operator_fee_fraction"], self.conf["pool-fee"])
        self.assertEqual(manifest["genesis_nonce"], 20261026)
        self.assertEqual(manifest["genesis_hash"],
                         "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c")
        # The public fee destination does not give the pool permission to run
        # or to claim ownership of the signing keys.
        self.assertFalse(manifest["release_authorized"])
        self.assertFalse(manifest["pool"]["payouts_enabled"])
        self.assertFalse(manifest["pool"]["stratum_public"])
        self.assertEqual(self.conf["pool-wallet"], "")
        self.assertEqual(self.conf["wallet-rpc-port"], "0")
        self.assertEqual(self.conf["disable-payouts"], "1")
        self.assertEqual(self.conf["pool-listen"], "127.0.0.1")
        self.assertEqual(self.conf["webui-listen"], "127.0.0.1")
        self.assertIn('if (!config.pool_fee_wallet[0])', self.pool)
        self.assertIn('fee_nettype != nettype', self.pool)
        self.assertIn('strcmp(config.pool_fee_wallet, config.pool_wallet) == 0', self.pool)

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
