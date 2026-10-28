#!/usr/bin/env python3
import base64
import copy
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from mfrg_signed_checkpoint_chain import verify_chain,fingerprint,payload,CheckpointError
def fixture():
    key=Ed25519PrivateKey.generate()
    pub=base64.b64encode(key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
    rows=[];prev=None
    for i in range(3):
        r={"version":1,"sequence":i,"previous_sha256":fingerprint(prev) if prev else None,"ledger_sha256":format(1+i,"064x"),
           "backup_sha256":format(20+i,"064x"),"consumed_count":i,"result_count":i}
        rows.append({"record":r,"signature_base64":base64.b64encode(key.sign(payload(r))).decode()})
        prev=r
    anchor={"sequence":1,"checkpoint_sha256":fingerprint(rows[1]["record"])}
    return rows,pub,anchor
class Tests(unittest.TestCase):
    def test_valid_and_explicit_limits(self):
        rows,key,anchor=fixture()
        result=verify_chain(rows,key,anchor)
        self.assertEqual(result["latest_sequence"],2)
        self.assertFalse(result["ledger_contents_compared_to_records"])
    def blocked(self,fn):
        rows,key,anchor=fixture()
        fn(rows,anchor)
        with self.assertRaises((CheckpointError,TypeError,ValueError)):verify_chain(rows,key,anchor)
    def test_tampered_hash(self):self.blocked(lambda r,a:r[2]["record"].update(ledger_sha256="0"*64))
    def test_tampered_signature(self):self.blocked(lambda r,a:r[2].update(signature_base64=base64.b64encode(bytes(64)).decode()))
    def test_missing_anchored_entry(self):self.blocked(lambda r,a:r.pop(1))
    def test_truncated_chain(self):self.blocked(lambda r,a:r.__delitem__(slice(1,None)))
    def test_reordered(self):self.blocked(lambda r,a:r.reverse())
    def test_sequence_gap(self):self.blocked(lambda r,a:r[2]["record"].update(sequence=5))
    def test_link_mismatch(self):self.blocked(lambda r,a:r[2]["record"].update(previous_sha256="0"*64))
    def test_count_rollback(self):self.blocked(lambda r,a:r[2]["record"].update(consumed_count=0))
    def test_anchor_tampered(self):self.blocked(lambda r,a:a.update(checkpoint_sha256="f"*64))
    def test_extra_field(self):self.blocked(lambda r,a:r[0]["record"].update(extra=True))
if __name__=="__main__":unittest.main()
