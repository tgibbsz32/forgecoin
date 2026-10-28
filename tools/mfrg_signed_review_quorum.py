#!/usr/bin/env python3
"""Step 30: offline Ed25519 reviewer signatures and explicitly pinned threshold.
Does not authenticate who controls keys or authorize treasury transactions.
"""
import base64,hashlib,json
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from mfrg_signed_checkpoint_chain import fingerprint,CheckpointError
DOMAIN=b"FORGECOIN-MFRG-REVIEW-V1\n"
def require(ok,message):
    if not ok: raise CheckpointError(message)
def canonical(obj):
    return DOMAIN+json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
def policy_digest(policy):
    return hashlib.sha256(json.dumps(policy,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def verify(export,policy,approvals,independent_policy_sha256):
    require(isinstance(policy,dict) and set(policy)=={"version","threshold","reviewers"},"policy schema")
    reviewers=policy["reviewers"];threshold=policy["threshold"]
    require(type(policy["version"]) is int and policy["version"]==1,"policy version")
    require(isinstance(reviewers,dict) and len(reviewers)>=2,"reviewer keys required")
    require(type(threshold) is int and 2<=threshold<=len(reviewers),"threshold invalid")
    require(isinstance(independent_policy_sha256,str) and policy_digest(policy)==independent_policy_sha256,"independent policy pin mismatch")
    require(isinstance(export,dict) and export.get("review_status")=="PENDING_INDEPENDENT_REVIEW","unsigned export required")
    record=export.get("record")
    require(isinstance(record,dict),"checkpoint missing")
    digest=fingerprint(record)
    require(export.get("record_fingerprint_sha256")==digest,"checkpoint fingerprint mismatch")
    required=export.get("reviewers_required")
    require(isinstance(required,list) and len(required)>=2 and len(set(required))==len(required) and set(required).issubset(reviewers),"reviewer allowlist invalid")
    require(isinstance(approvals,list),"approvals list required")
    seen=set()
    claim={"version":1,"checkpoint_sha256":digest,"policy_sha256":independent_policy_sha256}
    for item in approvals:
        require(isinstance(item,dict) and set(item)=={"reviewer_id","signature_base64"},"approval schema")
        rid=item["reviewer_id"]
        require(isinstance(rid,str) and rid in required and rid not in seen,"unknown or repeated reviewer")
        seen.add(rid)
        try:
            key=base64.b64decode(reviewers[rid],validate=True)
            signature=base64.b64decode(item["signature_base64"],validate=True)
            require(len(key)==32 and len(signature)==64,"key or signature length")
            Ed25519PublicKey.from_public_bytes(key).verify(signature,canonical(claim))
        except (InvalidSignature,ValueError,TypeError) as exc:
            raise CheckpointError("invalid reviewer signature") from exc
    require(len(seen)>=threshold,"insufficient signed review threshold")
    return {"status":"OFFLINE_SIGNED_REVIEW_QUORUM_ONLY","valid_reviewer_signatures":len(seen),
        "threshold":threshold,"policy_pin_matches":True,"independent_signer_identity_verified":False,
        "checkpoint_signing_performed":False,"sale_authorized":False,"treasury_release_authorized":False}
