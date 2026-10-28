#!/usr/bin/env python3
import sqlite3, tempfile, os, unittest
from mfrg_checkpoint_review_export import prepare,review,CheckpointError
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=os.path.join(self.tmp.name,"a.db")
  with sqlite3.connect(self.path) as db:
   db.executescript("""CREATE TABLE sessions(id TEXT,claim_json TEXT,status TEXT);
    CREATE TABLE nonces(nonce TEXT,session_id TEXT);
    CREATE TABLE results(session_id TEXT,request_hash TEXT,result_json TEXT);
    INSERT INTO sessions VALUES('id','{}','consumed');
    INSERT INTO results VALUES('id','hash','{}');""")
 def tearDown(self):self.tmp.cleanup()
 def export(self):return prepare(self.path,0,None,["reviewer-a","reviewer-b"])
 def approvals(self,e):return [{"reviewer_id":x,"record_fingerprint_sha256":e["record_fingerprint_sha256"],"decision":"approve"} for x in ("reviewer-a","reviewer-b")]
 def test_export(self):
  e=self.export();self.assertFalse(e["signing_performed"])
 def test_review_declarations_not_signatures(self):
  e=self.export();r=review(e,self.approvals(e),e["record_fingerprint_sha256"]);self.assertFalse(r["reviewer_signatures_cryptographically_verified"])
 def test_missing_review(self):
  e=self.export()
  with self.assertRaises(CheckpointError):review(e,self.approvals(e)[:1],e["record_fingerprint_sha256"])
 def test_duplicate_review(self):
  e=self.export();a=self.approvals(e);a[1]=a[0]
  with self.assertRaises(CheckpointError):review(e,a,e["record_fingerprint_sha256"])
 def test_wrong_fingerprint(self):
  e=self.export()
  with self.assertRaises(CheckpointError):review(e,self.approvals(e),"0"*64)
 def test_changed_record(self):
  e=self.export();e["record"]["consumed_count"]=3
  with self.assertRaises(CheckpointError):review(e,self.approvals(e),e["record_fingerprint_sha256"])
 def test_missing_previous(self):
  with self.assertRaises(CheckpointError):prepare(self.path,1,None,["reviewer-a","reviewer-b"])
 def test_duplicate_reviewers(self):
  with self.assertRaises(CheckpointError):prepare(self.path,0,None,["same","same"])
if __name__=="__main__":unittest.main()
