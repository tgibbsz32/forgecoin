#!/usr/bin/env python3
import copy
import hashlib
import unittest
from verify_mfrg_evidence_bundle import validate,EvidenceError
def example():
    files={"one.json":b"RPC_A","two.json":b"RPC_B","snapshot.db":b"SQLITE_BACKUP_BYTES"}
    hashes={k:hashlib.sha256(v).hexdigest() for k,v in files.items()}
    b={"version":1,"network":"solana-mainnet-beta","mint":"A"*43,
       "initialization_signature":"B"*88,
       "sources":[{"id":"a","origin":"https://host-one.example","slot":123,"commitment":"finalized","artifact":"one.json"},
                  {"id":"b","origin":"https://host-two.example","slot":124,"commitment":"finalized","artifact":"two.json"}],
       "artifacts":hashes,
       "backup":{"snapshot_file":"snapshot.db","sha256":hashes["snapshot.db"],"size_bytes":len(files["snapshot.db"])}}
    return b,files
class Tests(unittest.TestCase):
    def test_valid_but_not_authenticated(self):
        b,f=example();r=validate(b,f)
        self.assertFalse(r["mint_authenticated"]);self.assertFalse(r["backup_restore_tested"])
    def blocked(self,fn):
        b,f=example();fn(b,f)
        with self.assertRaises((EvidenceError,TypeError,KeyError)): validate(b,f)
    def test_mismatched_digest(self):self.blocked(lambda b,f:f.update({"one.json":b"tampered"}))
    def test_missing_artifact(self):self.blocked(lambda b,f:f.pop("two.json"))
    def test_duplicate_origin(self):self.blocked(lambda b,f:b["sources"][1].update(origin="https://host-one.example"))
    def test_duplicate_source(self):self.blocked(lambda b,f:b["sources"][1].update(id="a"))
    def test_wrong_commitment(self):self.blocked(lambda b,f:b["sources"][0].update(commitment="confirmed"))
    def test_wrong_network(self):self.blocked(lambda b,f:b.update(network="devnet"))
    def test_devnet_mint(self):self.blocked(lambda b,f:b.update(mint="9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw"))
    def test_backup_size(self):self.blocked(lambda b,f:b["backup"].update(size_bytes=0))
    def test_backup_hash(self):self.blocked(lambda b,f:b["backup"].update(sha256="0"*64))
    def test_unsafe_name(self):self.blocked(lambda b,f:b["artifacts"].update({"../evil":hashlib.sha256(b"").hexdigest()}))
    def test_missing_slot(self):self.blocked(lambda b,f:b["sources"][0].update(slot=0))
if __name__=="__main__":unittest.main()
