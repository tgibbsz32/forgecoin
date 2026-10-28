#!/usr/bin/env python3
"""Step 26 offline SQLite backup + isolated restore drill, with externally pinned checkpoint.
Never overwrites production DB. A caller-supplied anchor is NOT authenticated by this tool.
"""
import argparse
import hashlib
import json
import pathlib
import sqlite3
import tempfile

class RecoveryError(ValueError): pass
def require(ok,msg):
    if not ok: raise RecoveryError(msg)
def sha(data): return hashlib.sha256(data).hexdigest()

def checkpoint(conn):
    tables={}
    for name in ("sessions","nonces","results"):
        exists=conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone()
        require(exists is not None,"missing table "+name)
        tables[name]=conn.execute('SELECT COUNT(*) FROM "'+name+'"').fetchone()[0]
    consumed=conn.execute("SELECT COUNT(*) FROM sessions WHERE status='consumed'").fetchone()[0]
    require(tables["results"]==consumed,"result/consumed count mismatch")
    require(conn.execute("PRAGMA integrity_check").fetchone()[0]=="ok","SQLite integrity check failed")
    # Counts are an operational checkpoint, not proof against altered rows.
    return {"tables":tables,"consumed":consumed}

def drill(source_path,expected_anchor=None):
    source=pathlib.Path(source_path)
    require(source.is_file(),"source SQLite DB absent")
    with tempfile.TemporaryDirectory(prefix="mfrg-restore-") as temp:
        target=pathlib.Path(temp)/"restored.sqlite"
        with sqlite3.connect(f"file:{source}?mode=ro",uri=True) as src:
            before=checkpoint(src)
            with sqlite3.connect(target) as dst: src.backup(dst)
        raw=target.read_bytes()
        digest=sha(raw)
        with sqlite3.connect(f"file:{target}?mode=ro",uri=True) as restored:
            after=checkpoint(restored)
        require(before==after,"restored checkpoint differs")
        if expected_anchor is not None:
            require(isinstance(expected_anchor,dict) and set(expected_anchor)=={"consumed_at_least","results_at_least","backup_sha256"},"anchor schema")
            require(type(expected_anchor["consumed_at_least"]) is int and type(expected_anchor["results_at_least"]) is int,"invalid checkpoint counters")
            require(after["consumed"]>=expected_anchor["consumed_at_least"] and after["tables"]["results"]>=expected_anchor["results_at_least"],"rollback detected by anchored lower bounds")
            require(digest==expected_anchor["backup_sha256"],"pinned restored-backup digest mismatch")
        return {"status":"ISOLATED_SQLITE_RESTORE_VALIDATED_NOT_PRODUCTION_APPROVAL",
                "checkpoint":after,"restored_backup_sha256":digest,
                "independent_anchor_authenticated":False,
                "cross_host_rollback_prevention":False,
                "sale_authorized":False,"treasury_release_authorized":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("sqlite_database")
    p.add_argument("--anchor-json",help="optional externally authenticated checkpoint; validation alone cannot authenticate it")
    a=p.parse_args()
    try:
        anchor=json.loads(pathlib.Path(a.anchor_json).read_text()) if a.anchor_json else None
        print(json.dumps(drill(a.sqlite_database,anchor),indent=2,sort_keys=True))
    except (OSError,ValueError,sqlite3.Error) as exc:
        p.exit(1,"BLOCKED: "+str(exc)+"\n")
if __name__=="__main__": main()
