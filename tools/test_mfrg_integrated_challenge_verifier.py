#!/usr/bin/env python3
import base64
import copy
import datetime as dt
import os
import tempfile
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from test_verify_mfrg_control_challenges import sample
from verify_mfrg_control_challenges import fingerprint,challenge_bytes
from mfrg_signed_challenge_issuer import canonical,IssuerError,Ledger
from mfrg_integrated_challenge_verifier import reserve_verified_issuer,verify_and_consume
NOW=dt.datetime(2026,10,28,17,0,tzinfo=dt.timezone.utc)
def b64(raw):return base64.b64encode(raw).decode()
def setup():
    m,t,e=sample()
    private=Ed25519PrivateKey.generate()
    key=b64(private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw))
    c=e["challenges"][0]["claim"]
    claim={"version":1,"network":"solana-mainnet-beta","mint":m["mint"],"initialization_signature":m["initialization_signature"],"slot":e["slot"],
           "session_id":"a"*64,"issued_utc":"2026-10-28T17:00:00Z","expires_utc":"2026-10-28T17:05:00Z",
           "nonces":{c["token_account"]:c["nonce"]}}
    envelope={"claim":claim,"signature_base64":b64(private.sign(canonical(claim)))}
    return m,t,e,envelope,key
class Tests(unittest.TestCase):
    def test_success_and_replay(self):
        m,t,e,env,key=setup()
        with tempfile.TemporaryDirectory() as temp:
            db=os.path.join(temp,"issuer.sqlite")
            reserve_verified_issuer(env,key,db,NOW)
            result=verify_and_consume(m,t,fingerprint(t),e,env,key,db,NOW)
            self.assertTrue(result["session_consumed"])
            self.assertFalse(result["live_chain_custody_verified"])
            with self.assertRaises(IssuerError):verify_and_consume(m,t,fingerprint(t),e,env,key,db,NOW)
    def test_missing_reservation(self):
        m,t,e,env,key=setup()
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(IssuerError):verify_and_consume(m,t,fingerprint(t),e,env,key,os.path.join(temp,"db"),NOW)
    def test_failed_proof_does_not_consume(self):
        m,t,e,env,key=setup()
        with tempfile.TemporaryDirectory() as temp:
            db=os.path.join(temp,"db");reserve_verified_issuer(env,key,db,NOW)
            damaged=copy.deepcopy(e);damaged["challenges"][0]["signature_base64"]=b64(bytes(64))
            with self.assertRaises(ValueError):verify_and_consume(m,t,fingerprint(t),damaged,env,key,db,NOW)
            result=verify_and_consume(m,t,fingerprint(t),e,env,key,db,NOW)
            self.assertTrue(result["session_consumed"])
    def test_nonce_mismatch(self):
        m,t,e,env,key=setup()
        with tempfile.TemporaryDirectory() as temp:
            db=os.path.join(temp,"db");reserve_verified_issuer(env,key,db,NOW)
            env["claim"]["nonces"]["C"*43]="f"*64
            with self.assertRaises(IssuerError):verify_and_consume(m,t,fingerprint(t),e,env,key,db,NOW)
    def test_wrong_snapshot_slot(self):
        m,t,e,env,key=setup()
        with tempfile.TemporaryDirectory() as temp:
            db=os.path.join(temp,"db");reserve_verified_issuer(env,key,db,NOW)
            e["slot"]+=1
            with self.assertRaises(IssuerError):verify_and_consume(m,t,fingerprint(t),e,env,key,db,NOW)
    def test_expired_envelope(self):
        m,t,e,env,key=setup()
        with tempfile.TemporaryDirectory() as temp:
            db=os.path.join(temp,"db");reserve_verified_issuer(env,key,db,NOW)
            with self.assertRaises(IssuerError):verify_and_consume(m,t,fingerprint(t),e,env,key,db,NOW+dt.timedelta(minutes=6))
    def test_bad_trust_pin_not_consumed(self):
        m,t,e,env,key=setup()
        with tempfile.TemporaryDirectory() as temp:
            db=os.path.join(temp,"db");reserve_verified_issuer(env,key,db,NOW)
            with self.assertRaises(ValueError):verify_and_consume(m,t,"0"*64,e,env,key,db,NOW)
            self.assertTrue(verify_and_consume(m,t,fingerprint(t),e,env,key,db,NOW)["session_consumed"])
if __name__=="__main__":unittest.main()
