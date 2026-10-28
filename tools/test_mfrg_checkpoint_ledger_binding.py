#!/usr/bin/env python3
import base64
import os
import sqlite3
import tempfile
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from mfrg_checkpoint_ledger_binding import inspect,validate,CheckpointError
from mfrg_signed_checkpoint_chain import payload,fingerprint
class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=os.path.join(self.temp.name,"ledger.sqlite")
        with sqlite3.connect(self.path) as db:
            db.executescript("""CREATE TABLE sessions(id TEXT PRIMARY KEY,claim_json TEXT,status TEXT);
            CREATE TABLE nonces(nonce TEXT PRIMARY KEY,session_id TEXT);
            CREATE TABLE results(session_id TEXT PRIMARY KEY,request_hash TEXT,result_json TEXT);
            INSERT INTO sessions VALUES('s1','{}','consumed');
            INSERT INTO nonces VALUES('n1','s1');
            INSERT INTO results VALUES('s1','hash','{}');""")
        key=Ed25519PrivateKey.generate()
        self.pub=base64.b64encode(key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
        facts=inspect(self.path)
        record={"version":1,"sequence":0,"previous_sha256":None,**facts}
        self.chain=[{"record":record,"signature_base64":base64.b64encode(key.sign(payload(record))).decode()}]
        self.anchor={"sequence":0,"checkpoint_sha256":fingerprint(record)}
    def tearDown(self):self.temp.cleanup()
    def test_valid(self):
        r=validate(self.path,self.chain,self.pub,self.anchor)
        self.assertTrue(r["ledger_contents_compared_to_records"])
        self.assertFalse(r["sale_authorized"])
    def test_modified_row_rejected(self):
        with sqlite3.connect(self.path) as db:db.execute("UPDATE results SET result_json='bad' WHERE session_id='s1'")
        with self.assertRaises(CheckpointError):validate(self.path,self.chain,self.pub,self.anchor)
    def test_missing_row_rejected(self):
        with sqlite3.connect(self.path) as db:db.execute("DELETE FROM nonces")
        with self.assertRaises(CheckpointError):validate(self.path,self.chain,self.pub,self.anchor)
    def test_changed_backup_bytes_rejected(self):
        with sqlite3.connect(self.path) as db:db.execute("VACUUM")
        with self.assertRaises(CheckpointError):validate(self.path,self.chain,self.pub,self.anchor)
    def test_wrong_anchor(self):
        with self.assertRaises(CheckpointError):validate(self.path,self.chain,self.pub,{"sequence":0,"checkpoint_sha256":"0"*64})
if __name__=="__main__":unittest.main()
