import json,re,unittest,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
M=json.loads((R/"config/mainnet.identity.json").read_text())
def source(p):return (R/p).read_text(encoding="utf-8")
C=source("src/cryptonote_config.h")
D=source("src/cryptonote_basic/forgecoin_difficulty.h")
P=source("services/official_pool/jtgrassie/src/pool.c")
W=source("apps/desktop/Program.cs")
T=source("apps/desktop-tauri/src-tauri/src/engine.rs")
E=source("apps/explorer/app.py")
spec=importlib.util.spec_from_file_location("preflight",R/"tools/verify_mainnet.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ChainTest(unittest.TestCase):
 def test_nonce_uuid_exclusive(self):
  self.assertEqual(M["genesis_nonce"],20261026)
  self.assertIn("GENESIS_NONCE = 20261026",C)
  self.assertNotIn("GENESIS_NONCE = 20261020",C)
  self.assertEqual(M["network_uuid"],"bd936359-09e4-4fdb-8ec0-12fa9d6ef090")
  self.assertIn(", ".join("0x"+M["network_uuid"].replace("-","")[i:i+2] for i in range(0,32,2)),C)
  self.assertIn(M["genesis_tx_hex"],C)
  self.assertEqual(M["genesis_height"],0)
  self.assertFalse(M["release_authorized"])
 def test_economics(self):
  self.assertIn("50000000 * COIN",C)
  self.assertIn("CRYPTONOTE_DISPLAY_DECIMAL_POINT                8",C)
  for x in ("FORGE_STARTUP_INITIAL_DIFFICULTY = 500000","FORGE_MINIMUM_DIFFICULTY = 400000","FORGE_LWMA_HEIGHT = 16","FORGE_LWMA_WINDOW = 90"):
   self.assertIn(x,D)
  self.assertIn("{ 19, 1, 0, 1 }",source("src/hardforks/hardforks.cpp"))
 def test_network_integration(self):
  for x in ("P2P_DEFAULT_PORT = 39480","RPC_DEFAULT_PORT = 39481","ZMQ_RPC_DEFAULT_PORT = 39482","ADDRESS_BASE58_PREFIX = 190"):
   self.assertIn(x,C)
  self.assertIn("#define MAINNET_ADDRESS_PREFIX 190",P)
  self.assertIn("rpc-port = 39481",source("services/official_pool/jtgrassie/pool.conf"))
  self.assertIn("EXPECTED_GENESIS_NONCE = 20261026",E)
  self.assertIn("genesis.get('nonce') != EXPECTED_GENESIS_NONCE",E)
 def test_desktops_do_not_reuse_chain_data(self):
  for x in ("blockchain-mainnet-20261026","wallets-mainnet-20261026","ringdb-mainnet-20261026"):self.assertIn(x,W)
  for x in ("chain-mainnet-20261026","wallets-mainnet-20261026",'settings.peer.ends_with(":19480")'):self.assertIn(x,T)
  self.assertNotIn("http://127.0.0.1:19481",W)
  self.assertNotIn("http://127.0.0.1:19481",T)
 def test_pool_fee_destination_mandatory(self):
  for x in ("if (!config.pool_fee_wallet[0])","fee_nettype != nettype",'strcmp(config.pool_fee_wallet, config.pool_wallet) == 0'):
   self.assertIn(x,P)
  self.assertNotIn("Invalid fee wallet; ignoring",P)
  self.assertFalse(M["pool"]["payouts_enabled"])
 def test_preflight_refuses_wrong_nonce_and_mining(self):
  genesis={"height":0,"nonce":20261026,"hash":M["genesis_hash"]}
  state={"height":1,"nettype":"mainnet"}
  self.assertTrue(module.audit(M,state,genesis,require_launch_hash=False)["genesis_hash_frozen"])
  with self.assertRaises(ValueError):module.audit(M,state,{**genesis,"hash":"a"*64})
  for nonce in (10000,20261020):
   with self.assertRaises(ValueError):module.audit(M,state,{**genesis,"nonce":nonce},require_launch_hash=False)
  with self.assertRaises(ValueError):module.audit(M,{**state,"height":3},genesis,require_launch_hash=False)
  with self.assertRaises(ValueError):module.audit({**M,"genesis_hash":"b"*64},state,genesis)
if __name__=="__main__": unittest.main()
