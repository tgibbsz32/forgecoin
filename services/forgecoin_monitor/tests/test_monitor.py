import importlib.util
import pathlib
import unittest
from unittest import mock

script = pathlib.Path(__file__).resolve().parents[1] / "monitor.py"
spec = importlib.util.spec_from_file_location("frg_monitor", script)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)

def info():
    return {"nettype":"mainnet","height":1, "difficulty":500000,
            "outgoing_connections_count":0,"incoming_connections_count":0,
            "tx_pool_size":0, "synchronized":False, "top_block_hash":"a"*64}

def genesis():
    return {"block_header":{"height":0,"nonce":20261026, "hash":monitor.GENESIS_HASH}}

class MonitorTests(unittest.TestCase):
    def test_frozen_genesis_only(self):
        got = monitor.normalized_chain(info(), genesis())
        self.assertEqual(got["height"],1)
        self.assertEqual(got["minedBlocks"],0)
        self.assertEqual(got["peers"],0)

    def test_retired_genesis_rejected(self):
        g = genesis()
        g["block_header"]["nonce"] = 20261020
        with self.assertRaises(ValueError): monitor.normalized_chain(info(), g)

    def test_wrong_hash_rejected(self):
        g = genesis()
        g["block_header"]["hash"] = "0"*64
        with self.assertRaises(ValueError): monitor.normalized_chain(info(), g)

    def test_nonmainnet_rejected(self):
        i=info()
        i["nettype"]="testnet"
        with self.assertRaises(ValueError): monitor.normalized_chain(i,genesis())

    def test_pool_balances_are_dropped(self):
        raw = dict(pool_hashrate=23, network_hashrate=43, network_difficulty=100,
                   network_height=1, connected_miners=0, pool_blocks_found=0,
                   round_hashes=0, last_block_found=0,last_template_fetched=0,
                   pool_fee=.01, miner_balance=99999, pool_wallet="SECRET")
        x = monitor.normalized_pool(raw)
        self.assertEqual(x["poolFeePercent"],1)
        self.assertEqual(x["poolHashrate"],23)
        self.assertNotIn("miner_balance",x)
        self.assertNotIn("pool_wallet",x)

    def test_pool_rejects_fake_numbers(self):
        raw = dict.fromkeys(monitor.POOL_FIELDS.keys(),0)
        raw["pool_fee"]=.01
        raw["connected_miners"]=True
        with self.assertRaises(ValueError):monitor.normalized_pool(raw)

    def test_solo_does_not_expose_wallet(self):
        x = monitor.normalized_solo({"active":True,"speed":1750,"threads_count":2,
                                      "address":"DO_NOT_SEND","private_key":"NO"})
        self.assertEqual(set(x),{"active","hashrateHps","threads"})
        self.assertTrue(x["active"])

    def test_node_down_fails_closed(self):
        with mock.patch.object(monitor,"rpc",side_effect=ConnectionRefusedError()):
            got=monitor.snapshot()
        self.assertIsNone(got["network"])
        self.assertIsNone(got["pool"])
        self.assertIsNone(got["solo"])
        self.assertNotIn("verified",got["status"])

if __name__=="__main__":
    unittest.main()
