"""Read-only ForgeCoin explorer API fixture checks against production-identical code.
No daemon/network mining or wallet RPC use. Uses Flask test client and mocked local daemon results.
"""
import importlib.util,json,pathlib,unittest,time,os
HERE=pathlib.Path(__file__).resolve().parent
APP=pathlib.Path(os.environ.get("FORGE_EXPLORER_SOURCE", str(HERE/"app.py")))
spec=importlib.util.spec_from_file_location("frg_explorer_qa",APP)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
# Explicit static test fixture path because this module is dynamically imported by a non-package name.
module.app.static_folder=str(APP.parent / "static")
HASH=module.EXPECTED_GENESIS_HASH
NOW=1793080000
class ExplorerChecks(unittest.TestCase):
    def setUp(self):
        module.cache.clear()
        self.client=module.app.test_client()
        def mock_node(method,params=None,direct=False):
            if method=="get_info":
                return {"height":1,"nettype":"mainnet","synchronized":True,
                    "top_block_hash":HASH,"difficulty":500000,"target":120,"tx_pool_size":0,
                    "incoming_connections_count":0,"outgoing_connections_count":0}
            if method=="get_block_header_by_height":
                return {"block_header":{"height":0,"nonce":20261026,"hash":HASH}}
            if method=="get_block_headers_range":
                return {"headers":[{"height":0,"hash":HASH,"timestamp":NOW,
                    "difficulty":500000,"cumulative_difficulty":500000,
                    "reward":1192092895,"num_txes":0,"block_size":120,
                    "major_version":16,"prev_hash":"0"*64,"orphan_status":False}]}
            if method=="get_block":
                return {"block_header":{"height":0,"hash":HASH,"timestamp":NOW,
                    "difficulty":500000,"reward":1192092895,"num_txes":0,"block_size":120,
                    "major_version":16,"prev_hash":"0"*64,"orphan_status":False},
                    "miner_tx_hash":"1"*64,"tx_hashes":[]}
            if method=="get_transactions":
                return {"txs":[{"in_pool":False,"block_height":0,"confirmations":1,
                  "block_timestamp":NOW,"pruned_as_hex":"aabb",
                  "as_json":json.dumps({"vin":[{"key":{}}],"vout":[],"version":2,
                      "unlock_time":0,"rct_signatures":{"txnFee":12345}})}]}
            raise AssertionError("Unexpected arbitrary RPC method "+method)
        module.node=mock_node
    def test_01_correct_frozen_genesis_overview(self):
        rsp=self.client.get("/api/overview")
        self.assertEqual(rsp.status_code,200,rsp.json)
        self.assertEqual(rsp.json["height"],1)
        self.assertEqual(rsp.json["tip_hash"],HASH)
        self.assertEqual(rsp.json["blocks"][0]["reward_atomic"],"1192092895")
    def test_02_readonly_verb_gates(self):
        self.assertEqual(self.client.post("/api/overview").status_code,405)
        self.assertEqual(self.client.post("/api/tx/"+"0"*64).status_code,405)
        self.assertEqual(self.client.post("/api/block/0").status_code,405)
    def test_03_block_pagination_and_lookup(self):
        self.assertEqual(self.client.get("/api/blocks").status_code,200)
        self.assertEqual(self.client.get("/api/blocks").json["blocks"][0]["hash"],HASH)
        self.assertEqual(self.client.get("/api/block/0").json["confirmations"],1)
    def test_04_malformed_input_is_refused(self):
        self.assertEqual(self.client.get("/api/tx/not-a-hash").status_code,400)
        self.assertEqual(self.client.get("/api/blocks?before=00001").status_code,400)
        self.assertEqual(self.client.get("/api/blocks?before=999999999").status_code,404)
    def test_05_exact_chain_identity_guard(self):
        original=module.node
        def fake(method,params=None,direct=False):
            x=original(method,params,direct)
            if method=="get_block_header_by_height":
                x={"block_header":dict(x["block_header"])}
                x["block_header"]["hash"]="f"*64
            return x
        module.node=fake
        self.assertEqual(self.client.get("/api/overview").status_code,503)
    def test_06_native_node_offline_response(self):
        def unavailable(method,params=None,direct=False):
            raise module.Unavailable("simulated disconnected daemon")
        module.node=unavailable
        rsp=self.client.get("/api/overview")
        self.assertEqual(rsp.status_code,503)
        self.assertIn("offline or has an unrecognized genesis",rsp.json["error"])
    def test_07_confirmed_tx_lookup(self):
        txid="a"*64
        rsp=self.client.get("/api/tx/"+txid)
        self.assertEqual(rsp.status_code,200,rsp.json)
        self.assertEqual(rsp.json["hash"],txid)
        self.assertEqual(rsp.json["confirmations"],1)
        self.assertEqual(rsp.json["fee_atomic"],"12345")
    def test_08_http_security_headers(self):
        rsp=self.client.get("/api/overview")
        self.assertEqual(rsp.headers["X-Frame-Options"],"DENY")
        self.assertEqual(rsp.headers["X-Content-Type-Options"],"nosniff")
        self.assertEqual(rsp.headers["Cache-Control"],"no-store")
        self.assertIn("frame-ancestors 'none'",rsp.headers["Content-Security-Policy"])
    def test_09_prelaunch_status_is_public_and_not_an_activation_signal(self):
        rsp=self.client.get("/api/status")
        self.assertEqual(rsp.status_code,200)
        self.assertEqual(rsp.json["chain"],"forgecoin-mainnet")
        self.assertEqual(rsp.json["expected_genesis_hash"],HASH)
        self.assertEqual(rsp.json["expected_genesis_nonce"],20261026)
        self.assertEqual(rsp.json["expected_daemon_rpc_port"],39481)
        self.assertIs(rsp.json["public_launch_authorized"],False)
        self.assertIs(rsp.json["native_mining_enabled"],False)
        self.assertEqual(rsp.json["explorer_mode"],"prelaunch-read-only")
        self.assertIs(rsp.json["verified_native_node_connected"],True)
    def test_10_status_still_responds_when_node_is_down(self):
        def off(method,params=None,direct=False):
            raise module.Unavailable("offline fixture")
        module.node=off
        response=self.client.get("/api/status")
        self.assertEqual(response.status_code,200)
        self.assertIs(response.json["verified_native_node_connected"],False)
        self.assertIs(response.json["public_launch_authorized"],False)
    def test_11_legacy_chain_cannot_serve_any_public_ledger_route(self):
        original=module.node
        called=[]
        def old_node(method,params=None,direct=False):
            called.append(method)
            if method=="get_info":
                data=original(method,params,direct)
                return dict(data,nettype="testnet")
            return original(method,params,direct)
        module.node=old_node
        for route in ["/api/overview","/api/blocks","/api/block/0",
                      "/api/block/"+HASH,"/api/tx/"+"a"*64]:
            with self.subTest(path=route):
                module.cache.clear()
                self.assertEqual(self.client.get(route).status_code,503)
        self.assertEqual(called.count("get_block"),0)
        self.assertEqual(called.count("get_transactions"),0)
        self.assertEqual(called.count("get_block_headers_range"),0)
    def test_12_wrong_genesis_nonce_blocks_all_ledger_paths(self):
        original=module.node
        def candidate(method,params=None,direct=False):
            result=original(method,params,direct)
            if method=="get_block_header_by_height":
                return {"block_header":dict(result["block_header"],nonce=20261020)}
            return result
        module.node=candidate
        for path in ("/api/overview","/api/blocks","/api/block/"+HASH,"/api/tx/"+"f"*64):
            with self.subTest(path=path):
                module.cache.clear()
                self.assertEqual(self.client.get(path).status_code,503)
    def test_13_static_landing_identifies_frozen_network(self):
        rsp=self.client.get("/")
        self.assertEqual(rsp.status_code,200)
        data=rsp.data.decode("utf-8")
        self.assertIn("PUBLIC LAUNCH NOT AUTHORIZED",data)
        self.assertIn("20261026",data)
        self.assertIn("no public",data.lower())
        rsp.close()
    def test_14_configured_rpc_is_new_chain_localhost_only(self):
        self.assertEqual(module.RPC_URL,"http://127.0.0.1:39481")
        self.assertEqual(module.EXPECTED_GENESIS_HASH,HASH)
        self.assertEqual(module.EXPECTED_GENESIS_NONCE,20261026)
if __name__=="__main__":
    unittest.main(verbosity=2)
