#!/usr/bin/env python3
"""Synthetic Ed25519 signatures only; no real mint, signer or RPC data."""
import base64
import copy
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from verify_mfrg_signed_attestations import verify, canonical, ReconciliationError

def b64(data): return base64.b64encode(data).decode("ascii")

def fixtures():
    keys = {role: Ed25519PrivateKey.generate() for role in ("owner","governance")}
    trust = {"trusted_signers": {role: {
        "role":role, "public_key_base64": b64(key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw))
    } for role,key in keys.items()}}
    m = {"schema_version":1,"network":"solana-mainnet-beta","token_program":"TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
         "decimals":6,"mint":"A"*43,"initialization_signature":"B"*88,"mint_supply_atomic":1000000,
         "accounts":[{"token_account":"C"*43,"amount_atomic":1000000,"purpose":"operations","beneficial_owner_verified":True}],
         "signed_attestations":[]}
    for role,key in keys.items():
        claim = {"version":1,"network":m["network"],"mint":m["mint"],"initialization_signature":m["initialization_signature"],
                 "token_account":"C"*43,"purpose":"operations","amount_atomic":1000000,"role":role}
        m["signed_attestations"].append({"signer_id":role,"claim":claim,"signature_base64":b64(key.sign(canonical(claim)))})
    return m, trust

class SignedTests(unittest.TestCase):
    def test_valid_signature_but_no_custody_proof(self):
        m,t=fixtures(); output=verify(m,t)
        self.assertEqual(output["valid_signatures"],2)
        self.assertFalse(output["onchain_control_verified"])
        self.assertFalse(output["sale_authorized"])
    def blocked(self, change):
        m,t=fixtures();change(m,t)
        with self.assertRaises((ReconciliationError, ValueError, TypeError)):
            verify(m,t)
    def test_tampered_amount(self): self.blocked(lambda m,t:m["signed_attestations"][0]["claim"].update(amount_atomic=2))
    def test_tampered_purpose(self): self.blocked(lambda m,t:m["signed_attestations"][0]["claim"].update(purpose="emergency"))
    def test_wrong_mint(self): self.blocked(lambda m,t:m["signed_attestations"][0]["claim"].update(mint="D"*43))
    def test_wrong_signature(self): self.blocked(lambda m,t:m["signed_attestations"][0].update(signature_base64=b64(bytes(64))))
    def test_missing_governance(self): self.blocked(lambda m,t:m["signed_attestations"].pop())
    def test_duplicate(self): self.blocked(lambda m,t:m["signed_attestations"].append(copy.deepcopy(m["signed_attestations"][0])))
    def test_wrong_role(self): self.blocked(lambda m,t:m["signed_attestations"][0].update(signer_id="governance"))
    def test_missing_trust(self): self.blocked(lambda m,t:t["trusted_signers"].pop("owner"))
    def test_wrong_balance(self): self.blocked(lambda m,t:m["accounts"][0].update(amount_atomic=500000))
    def test_beneficial_claim_without_review(self): self.blocked(lambda m,t:m["accounts"][0].update(beneficial_owner_verified=False))
    def test_bad_network(self): self.blocked(lambda m,t:m.update(network="devnet"))
    def test_bad_key(self): self.blocked(lambda m,t:t["trusted_signers"]["owner"].update(public_key_base64=b64(bytes(3))))
    def test_unsigned_extra(self): self.blocked(lambda m,t:m["accounts"].append({"token_account":"D"*43,"amount_atomic":0,"purpose":"liquidity","beneficial_owner_verified":True}))
    def test_claim_unknown_field(self): self.blocked(lambda m,t:m["signed_attestations"][0]["claim"].update(extra="x"))
if __name__=="__main__": unittest.main()
