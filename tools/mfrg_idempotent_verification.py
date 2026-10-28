#!/usr/bin/env python3
"""Step 24: atomic result retention and idempotent recovery, offline only.

Result retrieval requires the exact issuer claim plus the verifier's canonical
request digest; it does NOT repeat verification against current chain data.
"""
import hashlib
import json
import sqlite3
from mfrg_signed_challenge_issuer import IssuerError, Ledger, canonical, verify_envelope
from verify_mfrg_control_challenges import verify_control

def serialized(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)

def digest_request(manifest,trust,evidence,envelope,trust_pin):
    return hashlib.sha256(serialized({"manifest":manifest,"trust":trust,"evidence":evidence,"envelope":envelope,"trust_pin":trust_pin}).encode()).hexdigest()

def verify_persist(manifest,trust,pin,evidence,envelope,issuer_pubkey,db_path,now=None):
    claim=verify_envelope(envelope,issuer_pubkey,now)
    if claim["mint"]!=manifest.get("mint") or claim["initialization_signature"]!=manifest.get("initialization_signature") or claim["slot"]!=evidence.get("slot") or evidence.get("commitment")!="finalized":
        raise IssuerError("issuer snapshot mismatch")
    challenges=evidence.get("challenges",[])
    seen={}
    for item in challenges:
        c=item.get("claim",{})
        address=c.get("token_account")
        if address in seen:raise IssuerError("duplicate challenge account")
        seen[address]=c.get("nonce")
    if seen!=claim["nonces"]:raise IssuerError("signed issuer nonce mismatch")
    req_hash=digest_request(manifest,trust,evidence,envelope,pin)
    db=Ledger(db_path)
    try:
        db.db.execute("CREATE TABLE IF NOT EXISTS results (session_id TEXT PRIMARY KEY, request_hash TEXT NOT NULL, result_json TEXT NOT NULL)")
        db.db.execute("BEGIN IMMEDIATE")
        try:
            row=db.db.execute("SELECT claim_json,status FROM sessions WHERE id=?",(claim["session_id"],)).fetchone()
            if row is None or json.loads(row[0])!=claim:raise IssuerError("missing or altered reservation")
            previous=db.db.execute("SELECT request_hash,result_json FROM results WHERE session_id=?",(claim["session_id"],)).fetchone()
            if previous:
                if previous[0]!=req_hash:raise IssuerError("replay payload differs from committed request")
                if row[1]!="consumed":raise IssuerError("corrupt result/session state")
                result=json.loads(previous[1])
                db.db.execute("COMMIT")
                return result
            if row[1]!="reserved":raise IssuerError("consumed session missing committed result")
            report=verify_control(manifest,trust,pin,evidence)
            report.update(status="OFFLINE_IDEMPOTENT_RESULT_NOT_ONCHAIN_PROOF",session_consumed=True,
                          live_chain_custody_verified=False,sale_authorized=False,treasury_release_authorized=False)
            db.db.execute("INSERT INTO results VALUES (?,?,?)",(claim["session_id"],req_hash,serialized(report)))
            updated=db.db.execute("UPDATE sessions SET status='consumed' WHERE id=? AND status='reserved'",(claim["session_id"],)).rowcount
            if updated!=1:raise IssuerError("session consumption conflict")
            db.db.execute("COMMIT")
            return report
        except BaseException:
            db.db.execute("ROLLBACK")
            raise
    finally:
        db.close()
