#!/usr/bin/env python3
"""Step 22: authenticated signed challenge sessions with SQLite replay reservations.
No live RPC, minting, payments, or key custody. Caller must independently pin issuer key.
"""
import base64
import datetime as dt
import json
import secrets
import sqlite3
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

DOMAIN=b"FORGECOIN-MFRG-ISSUER-SESSION-V1\n"

class IssuerError(ValueError): pass

def require(ok,msg):
    if not ok: raise IssuerError(msg)

def canonical(obj):
    return DOMAIN+json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()

def utc(value):
    require(isinstance(value,str) and value.endswith("Z"),"UTC Z timestamp required")
    try: return dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as e: raise IssuerError("malformed UTC time") from e

def new_claim(mint,signature,slot,accounts,now=None):
    """Generate proposal for an external authorized signer; never loads a private key."""
    now=now or dt.datetime.now(dt.timezone.utc)
    require(isinstance(accounts,list) and len(accounts)>0 and len(set(accounts))==len(accounts),"distinct accounts required")
    require(type(slot) is int and slot>0,"positive finalized slot required")
    return {"version":1,"network":"solana-mainnet-beta","mint":mint,"initialization_signature":signature,
        "slot":slot,"session_id":secrets.token_hex(32),
        "issued_utc":now.isoformat(timespec="seconds").replace("+00:00","Z"),
        "expires_utc":(now+dt.timedelta(minutes=5)).isoformat(timespec="seconds").replace("+00:00","Z"),
        "nonces":{addr:secrets.token_hex(32) for addr in accounts}}

def verify_envelope(envelope,pinned_issuer_public_key_b64,now=None):
    require(isinstance(envelope,dict) and set(envelope)=={"claim","signature_base64"},"envelope schema")
    c=envelope["claim"]
    require(isinstance(c,dict) and set(c)=={"version","network","mint","initialization_signature","slot","session_id","issued_utc","expires_utc","nonces"},"claim schema")
    require(type(c["version"]) is int and c["version"]==1 and c["network"]=="solana-mainnet-beta","version/network")
    require(type(c["slot"]) is int and c["slot"]>0,"slot")
    require(isinstance(c["mint"],str) and len(c["mint"])>=32,"mint")
    require(isinstance(c["initialization_signature"],str) and len(c["initialization_signature"])>=64,"initialization signature")
    require(isinstance(c["session_id"],str) and len(c["session_id"])==64 and all(x in "0123456789abcdef" for x in c["session_id"]),"session id")
    require(isinstance(c["nonces"],dict) and c["nonces"],"account nonces")
    require(all(isinstance(k,str) and len(k)>=32 and isinstance(v,str) and len(v)==64 and all(ch in "0123456789abcdef" for ch in v) for k,v in c["nonces"].items()),"nonce schema")
    require(len(set(c["nonces"].values()))==len(c["nonces"]),"nonce collision")
    issued,expires=utc(c["issued_utc"]),utc(c["expires_utc"])
    now=now or dt.datetime.now(dt.timezone.utc)
    require(issued<=now<expires and dt.timedelta(0)<expires-issued<=dt.timedelta(minutes=5),"session expired, future or overlong")
    try:
        key=base64.b64decode(pinned_issuer_public_key_b64,validate=True)
        sig=base64.b64decode(envelope["signature_base64"],validate=True)
        require(len(key)==32 and len(sig)==64,"key/signature byte length")
        Ed25519PublicKey.from_public_bytes(key).verify(sig,canonical(c))
    except (ValueError,InvalidSignature,TypeError) as e: raise IssuerError("issuer signature verification failed") from e
    return c

class Ledger:
    """Single shared SQLite database. Multiple processes on same durable filesystem only."""
    def __init__(self,path):
        self.db=sqlite3.connect(path,timeout=15,isolation_level=None)
        self.db.execute("PRAGMA busy_timeout=15000")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, claim_json TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('reserved','consumed')))")
        self.db.execute("CREATE TABLE IF NOT EXISTS nonces (nonce TEXT PRIMARY KEY, session_id TEXT NOT NULL)")
    def reserve(self,claim):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            payload=json.dumps(claim,sort_keys=True,separators=(",",":"))
            self.db.execute("INSERT INTO sessions VALUES (?,?,'reserved')",(claim["session_id"],payload))
            for nonce in claim["nonces"].values():
                self.db.execute("INSERT INTO nonces VALUES (?,?)",(nonce,claim["session_id"]))
            self.db.execute("COMMIT")
        except (sqlite3.IntegrityError,sqlite3.Error):
            self.db.execute("ROLLBACK")
            raise IssuerError("session or nonce replay")
    def consume(self,claim):
        """Caller must verify owner challenges BEFORE marking consumption."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("SELECT claim_json,status FROM sessions WHERE id=?",(claim["session_id"],)).fetchone()
            require(row is not None and row[1]=="reserved" and json.loads(row[0])==claim,"session not reserved or already consumed")
            updated=self.db.execute("UPDATE sessions SET status='consumed' WHERE id=? AND status='reserved'",(claim["session_id"],)).rowcount
            require(updated==1,"session replay")
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
    def close(self):self.db.close()
