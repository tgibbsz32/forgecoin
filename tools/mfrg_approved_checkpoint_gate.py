#!/usr/bin/env python3
"""Step 31: verify approved checkpoint envelope without issuing a signing key.
Offline only. No transactions, signing requests or live mainnet conclusions.
"""
from mfrg_signed_review_quorum import verify as verify_reviews, CheckpointError
from mfrg_signed_checkpoint_chain import verify_chain, fingerprint
from mfrg_checkpoint_ledger_binding import validate as validate_ledger

def require(condition,message):
    if not condition:raise CheckpointError(message)

def gate(backup_path,export,review_policy,approvals,policy_pin,signed_chain,checkpoint_public_key,external_anchor):
    approved=verify_reviews(export,review_policy,approvals,policy_pin)
    record=export["record"]
    require(isinstance(signed_chain,list) and signed_chain,"signed checkpoint chain required")
    latest=signed_chain[-1]["record"]
    require(latest==record,"approved record differs from signed checkpoint")
    require(fingerprint(latest)==export["record_fingerprint_sha256"],"checkpoint fingerprint mismatch")
    chain_report=verify_chain(signed_chain,checkpoint_public_key,external_anchor)
    ledger_report=validate_ledger(backup_path,signed_chain,checkpoint_public_key,external_anchor)
    return {"status":"OFFLINE_APPROVED_CHECKPOINT_AND_LEDGER_MATCH_ONLY",
      "reviewer_signatures_verified":approved["valid_reviewer_signatures"],
      "reviewer_threshold":approved["threshold"],
      "checkpoint_count":chain_report["checkpoints_verified"],
      "ledger_contents_matched":ledger_report["ledger_contents_compared_to_records"],
      "checkpoint_private_key_loaded":False,
      "independent_public_key_authentication":False,
      "mainnet_mint_authenticated":False,
      "sale_authorized":False,"treasury_release_authorized":False}
