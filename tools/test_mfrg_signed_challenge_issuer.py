#!/usr/bin/env python3
"""Synthetic signed issuer, replay, expiration and SQLite tests."""
import base64
import copy
import datetime as dt
import os
import tempfile
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from mfrg_signed_challenge_issuer import new_claim,canonical,verify_envelope,Ledger,IssuerError

NOW=dt.datetime(2026,10,28,17,0,tzinfo=dt.timezone.utc)
def sample():
    private=Ed25519PrivateKey.generate()
    public=base64.b64encode(private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
    claim=new_claim("A"*43,"B"*88,123,["C"*43,"D"*43],NOW)
    envelope={"claim":claim,"signature_base64":base64.b64encode(private.sign(canonical(claim))).decode()}
    return private,public,envelope
class Tests(unittest.TestCase):
    def test_valid(self):
        _,key,e=sample();self.assertEqual(verify_envelope(e,key,NOW)["slot"],123)
    def test_db_reserve_consume_replay(self):
        _,key,e=sample();c=verify_envelope(e,key,NOW)
        with tempfile.TemporaryDirectory() as d:
            db=Ledger(os.path.join(d,"ledger.sqlite"))
            db.reserve(c)
            with self.assertRaises(IssuerError):db.reserve(c)
            db.consume(c)
            with self.assertRaises(IssuerError):db.consume(c)
            db.close()
            reopened=Ledger(os.path.join(d,"ledger.sqlite"))
            with self.assertRaises(IssuerError):reopened.reserve(c)
            reopened.close()
    def test_nonce_reuse_different_session(self):
        _,key,e=sample()
        with tempfile.TemporaryDirectory() as d:
            db=Ledger(os.path.join(d,"ledger.sqlite"));db.reserve(e["claim"])
            other=copy.deepcopy(e["claim"]);other["session_id"]="f"*64
            with self.assertRaises(IssuerError):db.reserve(other)
            db.close()
    def test_expiry(self):
        _,key,e=sample()
        with self.assertRaises(IssuerError):verify_envelope(e,key,NOW+dt.timedelta(minutes=6))
    def test_future(self):
        _,key,e=sample()
        with self.assertRaises(IssuerError):verify_envelope(e,key,NOW-dt.timedelta(seconds=1))
    def test_tamper(self):
        _,key,e=sample();e["claim"]["slot"]=124
        with self.assertRaises(IssuerError):verify_envelope(e,key,NOW)
    def test_untrusted_key(self):
        _,key,e=sample();_,wrong,_=sample()
        with self.assertRaises(IssuerError):verify_envelope(e,wrong,NOW)
    def test_bad_signature(self):
        _,key,e=sample();e["signature_base64"]=base64.b64encode(bytes(64)).decode()
        with self.assertRaises(IssuerError):verify_envelope(e,key,NOW)
    def test_no_reused_nonces(self):
        private,key,e=sample();v=next(iter(e["claim"]["nonces"].values()))
        e["claim"]["nonces"]["D"*43]=v
        e["signature_base64"]=base64.b64encode(private.sign(canonical(e["claim"]))).decode()
        with self.assertRaises(IssuerError):verify_envelope(e,key,NOW)
    def test_reject_long_ttl(self):
        private,key,e=sample();e["claim"]["expires_utc"]="2026-10-28T17:11:00Z"
        e["signature_base64"]=base64.b64encode(private.sign(canonical(e["claim"]))).decode()
        with self.assertRaises(IssuerError):verify_envelope(e,key,NOW)
    def test_unknown_extra(self):
        _,key,e=sample();e["claim"]["extra"]=True
        with self.assertRaises(IssuerError):verify_envelope(e,key,NOW)
    def test_wrong_network(self):
        private,key,e=sample();e["claim"]["network"]="devnet"
        e["signature_base64"]=base64.b64encode(private.sign(canonical(e["claim"]))).decode()
        with self.assertRaises(IssuerError):verify_envelope(e,key,NOW)
if __name__=="__main__":unittest.main()
