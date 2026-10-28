#!/usr/bin/env python3
"""Step 27: offline, externally anchored Ed25519 checkpoint-chain verification.
Never authenticates a mainnet mint or permits token transfers.
"""
import base64
import hashlib
import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

DOMAIN=b"FORGECOIN-MFRG-CHECKPOINT-V1\n"
class CheckpointError(ValueError): pass
def ensure(condition,message):
    if not condition:raise CheckpointError(message)
def payload(record):
    return DOMAIN+json.dumps(record,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
def fingerprint(record):
    return hashlib.sha256(payload(record)).hexdigest()
def verify_chain(records,pinned_key_b64,anchor):
    ensure(isinstance(records,list) and len(records)>0,"nonempty chain required")
    ensure(isinstance(anchor,dict) and set(anchor)=={"sequence","checkpoint_sha256"},"independently pinned anchor required")
    ensure(type(anchor["sequence"]) is int and anchor["sequence"]>=0,"anchor sequence invalid")
    ensure(isinstance(anchor["checkpoint_sha256"],str) and len(anchor["checkpoint_sha256"])==64,"anchor hash invalid")
    try:
        key=base64.b64decode(pinned_key_b64,validate=True)
        ensure(len(key)==32,"Ed25519 public key length")
        pub=Ed25519PublicKey.from_public_bytes(key)
    except (ValueError,TypeError) as e:raise CheckpointError("invalid pinned key") from e
    previous=None
    anchored=False
    for index,envelope in enumerate(records):
        ensure(isinstance(envelope,dict) and set(envelope)=={"record","signature_base64"},"envelope fields invalid")
        r=envelope["record"]
        ensure(isinstance(r,dict) and set(r)=={"version","sequence","previous_sha256","ledger_sha256","backup_sha256","consumed_count","result_count"},"record schema invalid")
        ensure(type(r["version"]) is int and r["version"]==1,"record version")
        ensure(type(r["sequence"]) is int and r["sequence"]>=0,"sequence invalid")
        ensure(type(r["consumed_count"]) is int and type(r["result_count"]) is int and r["consumed_count"]>=0 and r["result_count"]==r["consumed_count"],"counts invalid")
        for field in ("ledger_sha256","backup_sha256"):
            h=r[field]
            ensure(isinstance(h,str) and len(h)==64 and all(c in "0123456789abcdef" for c in h),"invalid content digest")
        if index==0:
            ensure(r["previous_sha256"] is None,"first checkpoint must be root")
        else:
            ensure(r["sequence"]==previous["sequence"]+1,"sequence gap/replay")
            ensure(r["previous_sha256"]==fingerprint(previous),"chain link mismatch")
            ensure(r["consumed_count"]>=previous["consumed_count"],"consumption rollback")
        try:
            signature=base64.b64decode(envelope["signature_base64"],validate=True)
            ensure(len(signature)==64,"signature length")
            pub.verify(signature,payload(r))
        except (ValueError,InvalidSignature,TypeError) as e:raise CheckpointError("invalid checkpoint signature") from e
        if r["sequence"]==anchor["sequence"]:
            ensure(fingerprint(r)==anchor["checkpoint_sha256"],"external anchor mismatch")
            anchored=True
        previous=r
    ensure(anchored,"independently anchored checkpoint not found; possible truncation")
    ensure(records[-1]["record"]["sequence"]>=anchor["sequence"],"rollback below anchor")
    return {"status":"OFFLINE_SIGNED_CHAIN_ONLY_NOT_LIVE_CUSTODY",
            "checkpoints_verified":len(records),"latest_sequence":previous["sequence"],
            "external_anchor_authenticity_verified":False,
            "ledger_contents_compared_to_records":False,
            "mainnet_mint_authenticated":False,"sale_authorized":False,"treasury_release_authorized":False}
