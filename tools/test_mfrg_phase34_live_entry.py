#!/usr/bin/env python3
import unittest
from mfrg_phase34_live_entry import build,PhaseEntryError
from mfrg_owner_deployment_intake import DEVNET_MINT
def intake():
 return {"version":1,"network":"solana-mainnet-beta",
 "mint":"1"*32,"initialization_signature":"1"*64,
 "owner_statement_url":"https://example.org/owner",
 "initialization_history_url":"https://history.example.org/tx",
 "independent_source_urls":["https://source-one.example.org/view","https://source-two.example.org/view"]}
class Tests(unittest.TestCase):
 def test_default_does_not_call_network(self):
  report=build(intake(),rpc=lambda *a: self.fail("RPC called"))
  self.assertFalse(report["live_reads_performed"])
  self.assertFalse(report["token_operations_authorized"])
 def test_missing_rpc_origins(self):
  with self.assertRaises(PhaseEntryError):build(intake(),live=True)
 def test_same_rpc_origin(self):
  with self.assertRaises((PhaseEntryError,ValueError)):build(intake(),"https://rpc.example.org","https://rpc.example.org",True)
 def test_same_hostname_different_port(self):
  with self.assertRaises((PhaseEntryError,ValueError)):build(intake(),"https://rpc.example.org","https://rpc.example.org:443",True)
 def test_devnet_rejected_before_rpc(self):
  obj=intake();obj["mint"]=DEVNET_MINT
  with self.assertRaises(ValueError):build(obj,live=True)
 def test_malformed_intake(self):
  with self.assertRaises(ValueError):build({},live=False)
if __name__=="__main__":unittest.main()
