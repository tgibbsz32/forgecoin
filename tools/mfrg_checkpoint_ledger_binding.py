#!/usr/bin/env python3
"""Offline Step 28: bind a SQLite backup's logical rows and raw bytes to a signed checkpoint.
No keys, chain RPC, production mutation or release authorization.
"""
import hashlib
import json
import pathlib
import sqlite3
from mfrg_signed_checkpoint_chain import verify_chain,CheckpointError

TABLES=("sessions","nonces","results")
def require(ok,msg):
    if not ok:raise CheckpointError(msg)
def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
def content_digest(conn):
    data={}
    for table in TABLES:
        info=conn.execute('PRAGMA table_info("'+table+'")').fetchall()
        require(info,"missing table: "+table)
        columns=[c[1] for c in info]
        rows=conn.execute('SELECT * FROM "'+table+'"').fetchall()
        data[table]={"columns":columns,"rows":sorted([list(r) for r in rows],key=lambda x:canonical(x))}
    require(conn.execute("PRAGMA integrity_check").fetchone()[0]=="ok","SQLite integrity failure")
    return hashlib.sha256(canonical(data)).hexdigest(),data
def inspect(db_path):
    path=pathlib.Path(db_path)
    require(path.is_file(),"backup missing")
    raw_sha=hashlib.sha256(path.read_bytes()).hexdigest()
    with sqlite3.connect("file:"+str(path.resolve())+"?mode=ro",uri=True) as conn:
        digest,content=content_digest(conn)
        consumed=sum(r[-1]=="consumed" for r in content["sessions"]["rows"])
        results=len(content["results"]["rows"])
        require(consumed==results,"consumed/results divergence")
        return {"ledger_sha256":digest,"backup_sha256":raw_sha,
                "consumed_count":consumed,"result_count":results}
def validate(db_path,envelopes,pinned_key,anchor):
    report=verify_chain(envelopes,pinned_key,anchor)
    current=inspect(db_path)
    latest=envelopes[-1]["record"]
    require(all(latest[k]==v for k,v in current.items()),"checkpoint does not match actual restored SQLite content")
    report.update(status="OFFLINE_RESTORED_LEDGER_BOUND_TO_SIGNED_CHECKPOINT",
                  ledger_contents_compared_to_records=True,
                  backup_bytes_compared_to_signed_digest=True,
                  independent_anchor_authenticated=False,
                  live_mainnet_mint_verified=False,
                  sale_authorized=False,treasury_release_authorized=False)
    return report
