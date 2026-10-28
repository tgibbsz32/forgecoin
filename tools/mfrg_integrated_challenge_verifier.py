#!/usr/bin/env python3
"""Step 23 offline integration. Signed issuer session + owner challenge + atomic consume.

Never authorizes mainnet custody or financial operations. One SQLite database on one
shared reliable filesystem only; issuer authentication is only as strong as pinned key.
"""
import datetime as dt
import json
import sqlite3
from mfrg_signed_challenge_issuer import verify_envelope, Ledger, IssuerError
from verify_mfrg_control_challenges import verify_control, ReconciliationError

def verify_and_consume(manifest, trust, trust_hash, evidence, issuer_envelope, issuer_pubkey, database, now=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    claim=verify_envelope(issuer_envelope,issuer_pubkey,now)
    if claim["mint"]!=manifest.get("mint") or claim["initialization_signature"]!=manifest.get("initialization_signature"):
        raise IssuerError("issuer mint/init does not match manifest")
    if claim["slot"]!=evidence.get("slot") or evidence.get("commitment")!="finalized":
        raise IssuerError("issuer slot or commitment mismatch")
    issued_nonces=claim["nonces"]
    challenged={}
    for item in evidence.get("challenges",[]):
        c=item.get("claim",{})
        address=c.get("token_account")
        if address in challenged:raise IssuerError("duplicate challenge account")
        challenged[address]=c.get("nonce")
    if challenged!=issued_nonces:raise IssuerError("challenge nonces do not match signed issuer envelope")
    report=verify_control(manifest,trust,trust_hash,evidence)
    db=Ledger(database)
    try:
        # Pre-existing reservation must match exactly; consume uses one IMMEDIATE transaction.
        db.consume(claim)
    finally:
        db.close()
    report["status"]="OFFLINE_INTEGRATED_VERIFICATION_CONSUMED_NOT_ONCHAIN_PROOF"
    report["session_consumed"]=True
    report["live_chain_custody_verified"]=False
    report["sale_authorized"]=False
    report["treasury_release_authorized"]=False
    return report

# Reservation belongs to the authenticated issuer before delivery. Calling
# Ledger.reserve() with unverified or client-authored claim is NOT supported.
def reserve_verified_issuer(envelope, pinned_pubkey, database, now=None):
    claim=verify_envelope(envelope,pinned_pubkey,now)
    db=Ledger(database)
    try:db.reserve(claim)
    finally:db.close()
    return claim["session_id"]
