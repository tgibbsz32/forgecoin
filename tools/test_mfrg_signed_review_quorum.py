#!/usr/bin/env python3
import base64,copy,sqlite3,tempfile,os,unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from mfrg_signed_review_quorum import verify,canonical,policy_digest,CheckpointError
from mfrg_checkpoint_review_export import prepare
def b64(x):return base64.b64encode(x).decode()
def fixture():
    tmp=tempfile.TemporaryDirectory();path=os.path.join(tmp.name,"db")
    with sqlite3.connect(path) as db:
        db.executescript("CREATE TABLE sessions(id TEXT,claim_json TEXT,status TEXT);CREATE TABLE nonces(nonce TEXT,session_id TEXT);CREATE TABLE results(session_id TEXT,request_hash TEXT,result_json TEXT);")
    keys={x:Ed25519PrivateKey.generate() for x in ("a","b","c")}
    policy={"version":1,"threshold":2,"reviewers":{k:b64(v.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)) for k,v in keys.items()}}
    export=prepare(path,0,None,["a","b","c"]);pin=policy_digest(policy)
    claim={"version":1,"checkpoint_sha256":export["record_fingerprint_sha256"],"policy_sha256":pin}
    approvals=[{"reviewer_id":k,"signature_base64":b64(v.sign(canonical(claim)))} for k,v in keys.items()]
    return tmp,export,policy,pin,approvals
class Tests(unittest.TestCase):
 def test_valid(self):
    tmp,e,p,pin,a=fixture()
    try:
        r=verify(e,p,a[:2],pin);self.assertEqual(r["valid_reviewer_signatures"],2);self.assertFalse(r["sale_authorized"])
    finally:tmp.cleanup()
 def blocked(self,edit):
    tmp,e,p,pin,a=fixture()
    try:
        pin=edit(e,p,a,pin) or pin
        with self.assertRaises((CheckpointError,ValueError,TypeError)):verify(e,p,a,pin)
    finally:tmp.cleanup()
 def test_missing(self):self.blocked(lambda e,p,a,pin:a.__delitem__(slice(1,None)))
 def test_duplicate(self):self.blocked(lambda e,p,a,pin:a.__setitem__(1,copy.deepcopy(a[0])))
 def test_tamper(self):self.blocked(lambda e,p,a,pin:e["record"].update(consumed_count=1))
 def test_signature(self):self.blocked(lambda e,p,a,pin:a[0].update(signature_base64=b64(bytes(64))))
 def test_policy_tamper(self):self.blocked(lambda e,p,a,pin:p.update(threshold=3))
 def test_wrong_pin(self):self.blocked(lambda e,p,a,pin:"0"*64)
 def test_untrusted_reviewer(self):self.blocked(lambda e,p,a,pin:a[0].update(reviewer_id="outsider"))
 def test_false_boolean_threshold(self):self.blocked(lambda e,p,a,pin:p.update(threshold=True))
 def test_threshold_too_low(self):self.blocked(lambda e,p,a,pin:p.update(threshold=1))
 def test_reviewer_key_modified(self):self.blocked(lambda e,p,a,pin:p["reviewers"].update(a=b64(bytes(32))))
if __name__=="__main__":unittest.main()
