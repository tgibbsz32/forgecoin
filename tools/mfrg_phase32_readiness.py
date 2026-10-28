#!/usr/bin/env python3
"""Step 32: fail-closed evidence-readiness decision; no RPC, key use or transactions."""
import argparse
import json
import sys

REQUIRED = (
    "owner_authenticated_mainnet_mint",
    "owner_authenticated_mint_initialization_transaction",
    "independently_corroborated_finalized_holder_snapshot",
    "authenticated_reviewer_key_registry",
    "authenticated_checkpoint_signer_registry",
    "independently_published_rollback_anchor",
    "account_owner_control_verified",
    "treasury_beneficial_ownership_verified",
    "multisig_and_pda_controls_audited",
    "external_security_review_completed",
    "legal_and_owner_release_approval",
)

def evaluate(evidence):
    if not isinstance(evidence,dict) or set(evidence)!={"version","evidence"} or type(evidence["version"]) is not int or evidence["version"]!=1:
        raise ValueError("invalid phase gate schema")
    claims=evidence["evidence"]
    if not isinstance(claims,dict) or set(claims)!=set(REQUIRED):
        raise ValueError("all required evidence names must be present, with no extras")
    # Markers are strictly informational; this tool does NOT cryptographically
    # authenticate the referenced evidence or authorize a release.
    for name,value in claims.items():
        if not isinstance(value,dict) or set(value)!={"reviewed","reference"} or type(value["reviewed"]) is not bool or not isinstance(value["reference"],str):
            raise ValueError("invalid evidence record: "+name)
        if value["reviewed"] and not value["reference"].strip():
            raise ValueError("claimed review missing reference: "+name)
    missing=[name for name in REQUIRED if not claims[name]["reviewed"]]
    return {
        "status":"EVIDENCE_REVIEW_INCOMPLETE" if missing else "DECLARED_EVIDENCE_REVIEW_COMPLETE_REQUIRES_INDEPENDENT_AUDIT",
        "missing_evidence":missing,
        "declarations_independently_authenticated":False,
        "production_readiness_cryptographically_proven":False,
        "minting_authorized":False,
        "presale_authorized":False,
        "treasury_transfers_authorized":False,
        "staking_authorized":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence_json")
    a=p.parse_args()
    try:
        with open(a.evidence_json,encoding="utf8") as f: result=evaluate(json.load(f))
        print(json.dumps(result,indent=2,sort_keys=True))
    except (ValueError,OSError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr);return 1
    return 0
if __name__=="__main__":raise SystemExit(main())
