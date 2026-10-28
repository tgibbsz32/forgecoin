#!/usr/bin/env python3
"""No-network synthetic Step 20 tests."""
import base64
import copy
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from test_verify_mfrg_signed_attestations import fixtures
from verify_mfrg_control_challenges import verify_control,fingerprint,challenge_bytes,ReconciliationError

def b64(b): return base64.b64encode(b).decode()
def base58(raw):
    alphabet="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n=int.from_bytes(raw,"big")
    s=""
    while n:
        n,r=divmod(n,58);s=alphabet[r]+s
    return "1"*(len(raw)-len(raw.lstrip(b"\0")))+s

def sample():
    m,t=fixtures()
    owner=Ed25519PrivateKey.generate()
    from cryptography.hazmat.primitives import serialization
    address=base58(owner.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw))
    a=m["accounts"][0]
    c={"version":1,"network":m["network"],"mint":m["mint"],"initialization_signature":m["initialization_signature"],"token_account":a["token_account"],"owner_key":address,
       "slot":123456,"nonce":"a"*64,"purpose":a["purpose"],"amount_atomic":a["amount_atomic"]}
    e={"mint":m["mint"],"initialization_signature":m["initialization_signature"],"slot":123456,"commitment":"finalized",
       "account_owner_keys":{a["token_account"]:address},
       "challenges":[{"claim":c,"signature_base64":b64(owner.sign(challenge_bytes(c)))}]}
    return m,t,e

class ChallengeTests(unittest.TestCase):
    def test_positive_has_no_onchain_claim(self):
        m,t,e=sample();r=verify_control(m,t,fingerprint(t),e)
        self.assertEqual(r["account_key_challenges_verified"],1)
        self.assertFalse(r["live_mint_or_holder_snapshot_verified"])
        self.assertFalse(r["treasury_release_authorized"])
    def blocked(self,fn):
        m,t,e=sample();pin=fingerprint(t);pin=fn(m,t,e,pin) or pin
        with self.assertRaises((ReconciliationError,TypeError,ValueError,OverflowError)): verify_control(m,t,pin,e)
    def test_bad_pin(self): self.blocked(lambda m,t,e,p:"0"*64)
    def test_modified_trust(self): self.blocked(lambda m,t,e,p:t["trusted_signers"].update(fake={"role":"owner","public_key_base64":"x"}))
    def test_wrong_slot(self): self.blocked(lambda m,t,e,p:e.update(slot=123457))
    def test_wrong_mint(self): self.blocked(lambda m,t,e,p:e.update(mint="D"*43))
    def test_wrong_signature(self): self.blocked(lambda m,t,e,p:e["challenges"][0].update(signature_base64=b64(bytes(64))))
    def test_wrong_owner(self): self.blocked(lambda m,t,e,p:e["account_owner_keys"].update({"C"*43:"1"*32}))
    def test_bad_nonce(self): self.blocked(lambda m,t,e,p:e["challenges"][0]["claim"].update(nonce="0"*64))
    def test_wrong_amount(self): self.blocked(lambda m,t,e,p:e["challenges"][0]["claim"].update(amount_atomic=2))
    def test_duplicate_challenge(self): self.blocked(lambda m,t,e,p:e["challenges"].append(copy.deepcopy(e["challenges"][0])))
    def test_no_finalized(self): self.blocked(lambda m,t,e,p:e.update(commitment="confirmed"))
    def test_missing_owner(self): self.blocked(lambda m,t,e,p:e.update(account_owner_keys={}))
    def test_bad_network(self): self.blocked(lambda m,t,e,p:e["challenges"][0]["claim"].update(network="devnet"))
    def test_extra_field(self): self.blocked(lambda m,t,e,p:e["challenges"][0]["claim"].update(extra="x"))
if __name__=="__main__": unittest.main()
