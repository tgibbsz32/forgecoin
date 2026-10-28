#!/usr/bin/env python3
"""Step 21: offline single-use challenge session gate; no network or financial writes.

Replay journal persists only after all checks succeed. Use one trusted local journal
under exclusive OS file lock; cross-host coordination is NOT provided.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import tempfile
import fcntl
from verify_mfrg_control_challenges import verify_control, ReconciliationError

def require(ok, why):
    if not ok: raise ReconciliationError(why)

def check_session(manifest, trust, pin, evidence, session, used, now):
    require(isinstance(session, dict), "session required")
    require(set(session) == {"session_id","created_utc","expires_utc","mint","initialization_signature","slot","nonces"}, "strict session schema required")
    require(session["mint"] == manifest["mint"] and session["initialization_signature"] == manifest["initialization_signature"], "session mint/init mismatch")
    require(type(session["slot"]) is int and session["slot"] == evidence["slot"], "session slot mismatch")
    require(isinstance(session["session_id"],str) and len(session["session_id"]) >= 32, "session ID too short")
    def timestamp(s):
        require(isinstance(s,str) and s.endswith("Z"),"UTC Z timestamps required")
        try: return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
        except ValueError as exc: raise ReconciliationError("invalid timestamp") from exc
    created,expires=timestamp(session["created_utc"]),timestamp(session["expires_utc"])
    require(created <= now < expires and (expires-created).total_seconds() <= 600, "expired, future, or overlong session")
    require(isinstance(session["nonces"],dict), "session nonces object required")
    claim_nonces={x["claim"]["token_account"]:x["claim"]["nonce"] for x in evidence["challenges"]}
    require(session["nonces"] == claim_nonces, "issued nonce/account mapping mismatch")
    require(len(set(claim_nonces.values())) == len(claim_nonces), "repeated nonce within session")
    require(session["session_id"] not in used["sessions"], "session replay")
    require(not set(claim_nonces.values()).intersection(used["nonces"]), "nonce replay")
    result=verify_control(manifest,trust,pin,evidence)
    result["status"]="OFFLINE_SINGLE_JOURNAL_REPLAY_GUARD_ONLY"
    result["live_chain_ownership_verified"]=False
    result["challenge_issuer_authenticity_verified"]=False
    result["cross_host_replay_prevention"]=False
    return result, {"sessions":[session["session_id"]], "nonces":list(claim_nonces.values())}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for v in ("manifest","trust_policy","evidence","session","journal"):ap.add_argument(v)
    ap.add_argument("--trusted-policy-sha256",required=True)
    ap.add_argument("--now-utc",help="test only: override clock; DO NOT use for production")
    a=ap.parse_args()
    try:
        with open(a.manifest) as f: manifest=json.load(f)
        with open(a.trust_policy) as f:trust=json.load(f)
        with open(a.evidence) as f:evidence=json.load(f)
        with open(a.session) as f:session=json.load(f)
        now=dt.datetime.now(dt.timezone.utc) if not a.now_utc else dt.datetime.fromisoformat(a.now_utc.replace("Z","+00:00"))
        journal=pathlib.Path(a.journal)
        journal.parent.mkdir(parents=True,exist_ok=True)
        lock=journal.with_name(journal.name+".lock")
        with open(lock,"a+") as handle:
            fcntl.flock(handle.fileno(),fcntl.LOCK_EX)
            used={"sessions":[],"nonces":[]}
            if journal.exists():
                with open(journal) as f:used=json.load(f)
            require(isinstance(used,dict) and isinstance(used.get("sessions"),list) and isinstance(used.get("nonces"),list),"journal corrupt")
            outcome,addition=check_session(manifest,trust,a.trusted_policy_sha256,evidence,session,used,now)
            used["sessions"].extend(addition["sessions"])
            used["nonces"].extend(addition["nonces"])
            fd,tmp=tempfile.mkstemp(dir=str(journal.parent),prefix=".mfrg-journal-")
            try:
                with os.fdopen(fd,"w") as out:
                    json.dump(used,out,sort_keys=True)
                    out.flush();os.fsync(out.fileno())
                os.replace(tmp,journal)
            finally:
                if os.path.exists(tmp):os.unlink(tmp)
            print(json.dumps(outcome,indent=2,sort_keys=True))
    except (ValueError,TypeError,OSError,KeyError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 1
    return 0
if __name__=="__main__":raise SystemExit(main())
