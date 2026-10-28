#!/usr/bin/env python3
import os
import sqlite3
import tempfile
import unittest
from mfrg_sqlite_recovery_drill import drill,RecoveryError

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.temp.name,"test.sqlite")
        self.db=sqlite3.connect(self.path)
        self.db.executescript("""
            CREATE TABLE sessions(id TEXT PRIMARY KEY, claim_json TEXT NOT NULL, status TEXT NOT NULL);
            CREATE TABLE nonces(nonce TEXT PRIMARY KEY, session_id TEXT NOT NULL);
            CREATE TABLE results(session_id TEXT PRIMARY KEY,request_hash TEXT NOT NULL,result_json TEXT NOT NULL);
            INSERT INTO sessions VALUES('session1','{}','consumed');
            INSERT INTO nonces VALUES('nonce1','session1');
            INSERT INTO results VALUES('session1','hash','{}');
        """)
        self.db.commit();self.db.close()
    def tearDown(self):self.temp.cleanup()
    def test_restore_roundtrip(self):
        result=drill(self.path)
        self.assertEqual(result["checkpoint"]["consumed"],1)
        self.assertFalse(result["sale_authorized"])
    def test_matching_anchor(self):
        result=drill(self.path)
        anchor={"consumed_at_least":1,"results_at_least":1,"backup_sha256":result["restored_backup_sha256"]}
        self.assertEqual(drill(self.path,anchor)["checkpoint"]["consumed"],1)
    def test_detect_rollback_floor(self):
        result=drill(self.path)
        anchor={"consumed_at_least":2,"results_at_least":1,"backup_sha256":result["restored_backup_sha256"]}
        with self.assertRaises(RecoveryError):drill(self.path,anchor)
    def test_detect_digest_mismatch(self):
        with self.assertRaises(RecoveryError):drill(self.path,{"consumed_at_least":0,"results_at_least":0,"backup_sha256":"0"*64})
    def test_missing_results(self):
        with sqlite3.connect(self.path) as db:db.execute("DELETE FROM results")
        with self.assertRaises(RecoveryError):drill(self.path)
    def test_missing_table(self):
        with sqlite3.connect(self.path) as db:db.execute("DROP TABLE nonces")
        with self.assertRaises(RecoveryError):drill(self.path)
    def test_invalid_anchor(self):
        with self.assertRaises(RecoveryError):drill(self.path,{"bad":1})
    def test_does_not_overwrite_source(self):
        original=open(self.path,"rb").read()
        drill(self.path)
        self.assertEqual(open(self.path,"rb").read(),original)
if __name__=="__main__":unittest.main()
