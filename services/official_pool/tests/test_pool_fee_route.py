"""Operator fee-route regression checks for FRG native mainnet.

These tests do not assert that the operator controls the receiving private key.
"""
import json
import pathlib
import re
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[3]
MANIFEST=json.loads((ROOT/"config/mainnet.identity.json").read_text(encoding="utf-8"))
CONF=(ROOT/"services/official_pool/jtgrassie/pool.conf").read_text(encoding="utf-8")
SOURCE=(ROOT/"services/official_pool/jtgrassie/src/pool.c").read_text(encoding="utf-8")

def conf(name):
    for line in CONF.splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k,v=line.split("=",1)
        if k.strip()==name:
            return v.strip()
    raise AssertionError("Required pool config key missing: "+name)

class OperatorFeeRoute(unittest.TestCase):
    def test_operator_fee_address_matches_frozen_manifest(self):
        address=MANIFEST["pool"]["operator_fee_address"]
        self.assertEqual(conf("pool-fee-wallet"), address)
        self.assertRegex(address, r"^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{97}$")

    def test_fee_is_exact_one_percent_per_allocation(self):
        self.assertEqual(MANIFEST["pool"]["operator_fee_fraction"], "0.01")
        self.assertEqual(conf("pool-fee"), "0.01")
        self.assertEqual(conf("share-mul"), "2.0")
        self.assertIn("frg_pool_fee_atomic(amount)", SOURCE)
        self.assertIn("balance_add(config.pool_fee_wallet, fee, txn)", SOURCE)
        self.assertIn("balance_add(share->address, amount, txn)", SOURCE)

    def test_zero_fee_from_solo_mining(self):
        # Fees are applied only by the pool reward allocation function,
        # never in native consensus or via the solo miner.
        payouts=SOURCE.split("payout_block(block_t *block, MDB_txn *parent)",1)[1].split("static int\nprocess_blocks",1)[0]
        self.assertIn("frg_pool_fee_atomic(amount)",payouts)
        self.assertNotIn("start_mining",payouts)
        self.assertNotIn("submit_block",payouts)

    def test_fee_wallet_separate_from_reward_wallet_and_release_disabled(self):
        self.assertEqual(conf("pool-wallet"), "")
        self.assertNotEqual(conf("pool-wallet"),conf("pool-fee-wallet"))
        self.assertEqual(conf("disable-payouts"),"1")
        self.assertEqual(MANIFEST["pool"]["payouts_enabled"],False)
        self.assertIn('strcmp(config.pool_fee_wallet, config.pool_wallet) == 0',SOURCE)
        self.assertIn('fee_nettype != nettype',SOURCE)
        self.assertIn('config.disable_hash_check || !config.disable_payouts',SOURCE)

    def test_eight_decimal_illustrative_fee_math(self):
        def fee(atomic):return atomic//100
        allocations=[100_000_000,33_000_000,238_418_522,1,0]
        for gross in allocations:
            operator=fee(gross)
            miner=gross-operator
            self.assertEqual(miner+operator,gross)
            self.assertGreaterEqual(miner,0)
            self.assertLessEqual(operator,gross)
        self.assertEqual(fee(100_000_000),1_000_000)
        self.assertEqual(100_000_000-fee(100_000_000),99_000_000)

if __name__=="__main__":
    unittest.main()
