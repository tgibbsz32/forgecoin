"""Read-only wallet + daemon canonical observation tests; no external RPC traffic."""
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from services.pool_settlement.ledger import Journal,SettlementError
from services.pool_settlement.verify_rpc import ReadOnlyRPCVerifier,loopback_only

A="YnJ4sygA2VbA4nvoXssZcSKh4fwsw4g3DaujrVCDXSwWGuXwnYTfNsKPVunwuAf8joPEWfePpMh6CEsyEqMpQz2i2uFy112XA"
B="YnJPKnrv2fk6MdHkvvAxDbe1L3Dv7WgtrjPBHnP3NokU1Zri6a8da9SfoDiF9SpQxP4Xn18BT2bBNLnVtCPqXTvr1UTsca4Z4"
TX="a"*64
HASH="b"*64
GENESIS="4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"
PAIRS=((A,9_900_000),(B,100_000))
BATCH="frg-qa-wallet-observer1"

class FakeRPC(ReadOnlyRPCVerifier):
    def __init__(self):
        super().__init__("http://127.0.0.1:39481","http://127.0.0.1:39483")
        self.mainnet=True
        self.tip=135
        self.confirmations=22
        self.height=115
        self.block_hash=HASH
        self.in_pool=False
        self.double=False
        self.wallet_type="out"
        self.destinations=PAIRS
        self.included=True
        self.canonical=True
        self.requested=[]

    def node(self,method,params=None):
        self.requested.append(("daemon",method))
        if method=="get_info":
            return {"nettype":"mainnet" if self.mainnet else "testnet","height":self.tip+1}
        if method=="get_block_header_by_height":
            if params["height"]==0:
                return {"block_header":{"hash":GENESIS,"nonce":20261026}}
            return {"block_header":{"hash":self.block_hash,"height":self.height}}
        if method=="get_transactions":
            return {"txs":[{"tx_hash":TX,"in_pool":self.in_pool,
                             "double_spend_seen":self.double,
                             "block_height":self.height}]}
        if method=="get_block":
            return {"block_header":{"hash":self.block_hash if self.canonical else "0"*64},
                    "json":json.dumps({"tx_hashes":[TX] if self.included else []})}
        raise AssertionError("unsafe/unexpected daemon RPC")

    def wallet_read(self,method,params=None):
        self.requested.append(("wallet",method))
        if method!="get_transfer_by_txid":raise AssertionError("unsafe wallet RPC")
        return {"transfer":{"txid":TX,"type":self.wallet_type,
                            "height":self.height,"confirmations":self.confirmations,
                            "locked":False,"double_spend_seen":self.double,
                            "destinations":[{"address":addr,"amount":units}
                                            for addr,units in self.destinations]}}

class ReadOnlyVerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="forge-wallet-observe-")
        self.j=Journal(pathlib.Path(self.tmp.name)/"journal.sqlite",qa_mode=True)
        self.j.credit_verified_mature_reward("1"*64,PAIRS,verified_canonical=True)
        self.j.reserve(BATCH,PAIRS)
        self.j.record_signed(BATCH,[TX],["beef"*20])
        self.j.record_relay_result(BATCH,acknowledged_txids=[TX])
        self.v=FakeRPC()
    def tearDown(self):
        self.j.close()
        self.tmp.cleanup()

    def test_loopback_rejects_external_services_and_embedded_auth(self):
        for url in ("http://0.0.0.0:39481","http://192.168.1.1:39481",
                    "https://127.0.0.1:39481","http://8.8.8.8:39481",
                    "http://example.com:39481","http://user:password@127.0.0.1:39483",
                    "http://127.0.0.1:39483/?password=no","http://127.0.0.1"):
            with self.subTest(url=url):
                with self.assertRaises(SettlementError):loopback_only(url)
        self.assertEqual(loopback_only("http://127.0.0.1:39481"),"http://127.0.0.1:39481")
    def test_fail_wrong_network(self):
        self.v.mainnet=False
        with self.assertRaises(SettlementError):self.v.verify_batch(self.j,BATCH)
        self.assertEqual(self.j.snapshot(BATCH)["state"],"BROADCAST")
    def test_verified_exact_canonical_outgoing_tx(self):
        self.assertEqual(self.v.verify_batch(self.j,BATCH),1)
        self.assertEqual(self.j.snapshot(BATCH)["state"],"OBSERVED")
        self.assertEqual(self.v.requested.count(("wallet","get_transfer_by_txid")),1)
        self.assertTrue(self.j.commit_observed(BATCH))
        self.assertEqual(self.j.balance(A),(0,0))
    def test_insufficient_confirmations(self):
        self.v.tip=118
        with self.assertRaises(SettlementError):self.v.verify_batch(self.j,BATCH)
        self.assertEqual(self.j.snapshot(BATCH)["state"],"BROADCAST")
    def test_wallet_claim_more_confirmations_than_daemon(self):
        self.v.tip=130
        self.v.confirmations=10_000
        self.assertRaises(SettlementError,self.v.verify_batch,self.j,BATCH) if self.v.tip-self.v.height+1<20 else self.assertEqual(self.v.verify_batch(self.j,BATCH),1)
    def test_wallet_height_over_tip(self):
        self.v.height=145
        with self.assertRaises(SettlementError):self.v.verify_batch(self.j,BATCH)
    def test_wallet_incoming_transaction_rejected(self):
        self.v.wallet_type="in"
        with self.assertRaises(SettlementError):self.v.verify_batch(self.j,BATCH)
    def test_mempool_and_double_spend_rejected(self):
        for key,val in [("in_pool",True),("double",True)]:
            setattr(self.v,key,val)
            with self.assertRaises(SettlementError):self.v.verify_batch(self.j,BATCH)
            setattr(self.v,key,False)
    def test_no_canonical_block_or_missing_inclusion(self):
        self.v.canonical=False
        with self.assertRaises(SettlementError):self.v.verify_batch(self.j,BATCH)
        self.v.canonical=True
        self.v.included=False
        with self.assertRaises(SettlementError):self.v.verify_batch(self.j,BATCH)
    def test_wrong_wallet_destinations_rejected(self):
        self.v.destinations=((A,10_000_000),)
        with self.assertRaises(SettlementError):self.v.verify_batch(self.j,BATCH)
        self.assertEqual(self.j.balance(A),(0,9_900_000))
    def test_unapproved_rpc_method_unavailable(self):
        with self.assertRaises(SettlementError):
            self.v._rpc(self.v.wallet,"transfer_split",{"destinations":[]},wallet=True)
        with self.assertRaises(SettlementError):
            self.v._rpc(self.v.daemon,"submit_block",{})
    def test_read_only_path_never_issues_create_sign_relay_or_send(self):
        self.v.verify_batch(self.j,BATCH)
        self.assertEqual([method for scope,method in self.v.requested if scope=="wallet"],
                         ["get_transfer_by_txid"])
        self.assertTrue(all(method in
            ("get_info","get_block_header_by_height","get_transactions","get_block")
            for scope,method in self.v.requested if scope=="daemon"))

if __name__=="__main__":unittest.main()
