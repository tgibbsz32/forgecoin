#!/usr/bin/env python3
import base64,os,sqlite3,tempfile,unittest,copy
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from mfrg_approved_checkpoint_gate import gate,CheckpointError
from mfrg_checkpoint_review_export import prepare
from mfrg_signed_checkpoint_chain import payload,fingerprint
from mfrg_signed_review_quorum import policy_digest,canonical
def b64(data):return base64.b64encode(data).decode()
def setup():
    folder=tempfile.TemporaryDirectory();path=os.path.join(folder.name,"a.sqlite")
    with sqlite3.connect(path) as db:
        db.executescript("CREATE TABLE sessions(id TEXT,claim_json TEXT,status TEXT);CREATE TABLE nonces(nonce TEXT,session_id TEXT);CREATE TABLE results(session_id TEXT,request_hash TEXT,result_json TEXT);")
    export=prepare(path,0,None,["a","b"])
    keys={x:Ed25519PrivateKey.generate() for x in ("a","b")}
    policy={"version":1,"threshold":2,"reviewers":{k:b64(v.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)) for k,v in keys.items()}}
    pin=policy_digest(policy)
    claim={"version":1,"checkpoint_sha256":export["record_fingerprint_sha256"],"policy_sha256":pin}
    approvals=[{"reviewer_id":k,"signature_base64":b64(v.sign(canonical(claim)))} for k,v in keys.items()]
    signer=Ed25519PrivateKey.generate()
    public=b64(signer.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw))
    record=export["record"]
    chain=[{"record":record,"signature_base64":b64(signer.sign(payload(record)))}]
    anchor={"sequence":0,"checkpoint_sha256":fingerprint(record)}
    return folder,path,export,policy,approvals,pin,chain,public,anchor
class Tests(unittest.TestCase):
 def test_end_to_end(self):
    f,path,e,p,a,pin,c,k,anchor=setup()
    try:
        result=gate(path,e,p,a,pin,c,k,anchor)
        self.assertTrue(result["ledger_contents_matched"])
        self.assertFalse(result["sale_authorized"])
    finally:f.cleanup()
 def blocked(self,change):
    f,path,e,p,a,pin,c,k,anchor=setup()
    try:
        change(e,p,a,c,anchor)
        with self.assertRaises((CheckpointError,ValueError)):gate(path,e,p,a,pin,c,k,anchor)
    finally:f.cleanup()
 def test_missing_review(self):self.blocked(lambda e,p,a,c,x:a.pop())
 def test_changed_checkpoint(self):self.blocked(lambda e,p,a,c,x:c[-1]["record"].update(consumed_count=2))
 def test_wrong_anchor(self):self.blocked(lambda e,p,a,c,x:x.update(checkpoint_sha256="0"*64))
 def test_tampered_approval(self):self.blocked(lambda e,p,a,c,x:a[0].update(signature_base64=b64(bytes(64))))
 def test_modified_export(self):self.blocked(lambda e,p,a,c,x:e["record"].update(result_count=2))
if __name__=="__main__":unittest.main()
