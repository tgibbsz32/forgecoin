#!/usr/bin/env python3
"""Offline Step 20: pinned trust registry and Solana owner-key challenge checks.

A signature only proves possession of a private key matching the supplied public key.
A Solana token account may be controlled by a PDA or multisig; this tool does not
prove those controls, beneficial ownership or live account state.
"""
import argparse
import base64
import hashlib
import json
import re
import sys
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from verify_mfrg_signed_attestations import verify, ReconciliationError

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
DOMAIN = b"FORGECOIN-MFRG-CONTROL-CHALLENGE-V1\n"
HEX = re.compile(r"^[a-f0-9]{64}$")

def require(cond, message):
    if not cond:
        raise ReconciliationError(message)

def pubkey_bytes(address):
    require(isinstance(address, str) and 32 <= len(address) <= 44, "invalid Solana public key")
    n = 0
    for ch in address:
        require(ch in ALPHABET, "invalid base58 public key")
        n = n * 58 + ALPHABET.index(ch)
    raw = n.to_bytes((n.bit_length() + 7)//8, "big") if n else b""
    raw = b"\0" * (len(address)-len(address.lstrip("1"))) + raw
    require(len(raw) == 32, "Solana public key must decode to 32 bytes")
    return raw

def decode64(value, length):
    require(isinstance(value, str), "base64 field missing")
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ReconciliationError("invalid base64") from exc
    require(len(raw) == length, "wrong encoded length")
    return raw

def fingerprint(trust):
    data = json.dumps(trust,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()

def challenge_bytes(claim):
    return DOMAIN + json.dumps(claim,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()

def verify_control(manifest, trust, pinned_hash, evidence):
    require(isinstance(pinned_hash, str) and HEX.fullmatch(pinned_hash) is not None, "independently pinned SHA256 required")
    require(fingerprint(trust) == pinned_hash, "trust registry does not match independent pin")
    result = verify(manifest, trust)
    require(isinstance(evidence, dict) and isinstance(evidence.get("challenges"), list), "challenges required")
    require(evidence.get("mint") == manifest["mint"], "snapshot mint mismatch")
    require(evidence.get("initialization_signature") == manifest["initialization_signature"], "initialization mismatch")
    require(type(evidence.get("slot")) is int and evidence["slot"] > 0, "finalized snapshot slot required")
    require(evidence.get("commitment") == "finalized", "finalized snapshot required")
    owners = evidence.get("account_owner_keys")
    require(isinstance(owners, dict), "account owner-key mapping required")
    assigned = {a["token_account"]: a for a in manifest["accounts"] if a["purpose"] != "unassigned"}
    require(set(owners) == set(assigned), "owner keys must cover exactly assigned accounts")
    challenges = evidence["challenges"]
    require(len(challenges) == len(assigned), "one challenge per assigned account required")
    seen=set()
    for c in challenges:
        require(isinstance(c,dict) and set(c)=={"claim","signature_base64"}, "challenge schema invalid")
        claim=c["claim"]
        require(isinstance(claim,dict) and set(claim)=={"version","network","mint","initialization_signature","token_account","owner_key","slot","nonce","purpose","amount_atomic"}, "challenge claim fields invalid")
        addr=claim["token_account"]
        require(addr in assigned and addr not in seen,"duplicate/unrecognized account challenge")
        seen.add(addr)
        account=assigned[addr]
        require(type(claim["version"]) is int and claim["version"]==1, "version invalid")
        require(claim["network"]=="solana-mainnet-beta" and claim["mint"]==manifest["mint"] and claim["initialization_signature"]==manifest["initialization_signature"], "claim not bound to mint")
        require(type(claim["slot"]) is int and claim["slot"]==evidence["slot"], "slot mismatch")
        require(claim["purpose"]==account["purpose"] and type(claim["amount_atomic"]) is int and claim["amount_atomic"]==account["amount_atomic"], "account binding mismatch")
        require(isinstance(claim["nonce"],str) and re.fullmatch(r"[a-f0-9]{64}",claim["nonce"]) is not None and claim["nonce"]!="0"*64, "256-bit nonce required")
        require(claim["owner_key"]==owners[addr], "owner mismatch against supplied snapshot")
        key=pubkey_bytes(claim["owner_key"])
        try:
            Ed25519PublicKey.from_public_bytes(key).verify(decode64(c["signature_base64"],64),challenge_bytes(claim))
        except (InvalidSignature,ValueError) as exc:
            raise ReconciliationError("invalid account-key challenge signature") from exc
    result.update({
       "status":"OFFLINE_PINNED_SIGNATURE_CHECK_ONLY",
       "trusted_registry_matches_out_of_band_pin":True,
       "account_key_challenges_verified":len(seen),
       "account_owner_keys_proven_against_live_chain":False,
       "challenge_freshness_and_nonce_uniqueness_across_runs_verified":False,
       "pda_and_multisig_control_verified":False,
       "live_mint_or_holder_snapshot_verified":False,
       "sale_authorized":False,
       "treasury_release_authorized":False
    })
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("trust_policy")
    parser.add_argument("snapshot_and_challenges")
    parser.add_argument("--trusted-policy-sha256",required=True,help="SHA256 from independently authenticated channel, NOT calculated from untrusted input during acceptance")
    args=parser.parse_args()
    try:
        with open(args.manifest,encoding="utf8") as f: manifest=json.load(f)
        with open(args.trust_policy,encoding="utf8") as f: trust=json.load(f)
        with open(args.snapshot_and_challenges,encoding="utf8") as f: evidence=json.load(f)
        print(json.dumps(verify_control(manifest,trust,args.trusted_policy_sha256,evidence),indent=2,sort_keys=True))
    except (OSError,ValueError,TypeError,OverflowError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 1
    return 0
if __name__=="__main__":
    raise SystemExit(main())
