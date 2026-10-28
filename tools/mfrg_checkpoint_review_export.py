#!/usr/bin/env python3
"""Offline Step 29 unsigned checkpoint export and independent review requirements.
No signing keys, network calls or transaction capability.
"""
import argparse
import hashlib
import json
from mfrg_checkpoint_ledger_binding import inspect
from mfrg_signed_checkpoint_chain import fingerprint, CheckpointError

def require(ok,msg):
    if not ok: raise CheckpointError(msg)
def prepare(db_path,sequence,previous_sha256,reviewers):
    require(type(sequence) is int and sequence >= 0,"sequence required")
    require(previous_sha256 is None if sequence == 0 else isinstance(previous_sha256,str) and len(previous_sha256)==64,"previous checkpoint digest required")
    require(isinstance(reviewers,list) and len(reviewers)>=2 and len(set(reviewers))==len(reviewers),"two distinct reviewer IDs required")
    require(all(isinstance(x,str) and x.strip() for x in reviewers),"reviewer ID invalid")
    facts=inspect(db_path)
    record={"version":1,"sequence":sequence,"previous_sha256":previous_sha256,**facts}
    return {"schema_version":1,"record":record,
            "record_fingerprint_sha256":fingerprint(record),
            "reviewers_required":reviewers,"review_status":"PENDING_INDEPENDENT_REVIEW",
            "signing_performed":False,"deployment_authorized":False}
def review(export, approvals, expected_fingerprint):
    require(isinstance(export,dict) and export.get("review_status")=="PENDING_INDEPENDENT_REVIEW","export invalid")
    require(export.get("record_fingerprint_sha256")==expected_fingerprint==fingerprint(export["record"]),"fingerprint mismatch")
    allowed=export.get("reviewers_required")
    require(isinstance(allowed,list) and len(allowed)>=2,"reviewer policy invalid")
    require(isinstance(approvals,list) and len(approvals)>=2,"at least two signed-off records required")
    ids=set()
    for a in approvals:
        require(isinstance(a,dict) and set(a)=={"reviewer_id","record_fingerprint_sha256","decision"},"review fields")
        identifier=a["reviewer_id"]
        require(identifier in allowed and identifier not in ids,"unknown or repeated reviewer")
        require(a["record_fingerprint_sha256"]==expected_fingerprint and a["decision"]=="approve","approval mismatched")
        ids.add(identifier)
    return {"status":"UNSIGNED_OFFLINE_REVIEW_DECLARATIONS_ONLY",
            "reviewers_declared":len(ids),
            "reviewer_signatures_cryptographically_verified":False,
            "checkpoint_signed":False,"sale_authorized":False,"treasury_release_authorized":False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("db");p.add_argument("--sequence",type=int,required=True);p.add_argument("--previous-sha256")
    p.add_argument("--reviewer",action="append",required=True)
    args=p.parse_args()
    try:print(json.dumps(prepare(args.db,args.sequence,args.previous_sha256,args.reviewer),indent=2,sort_keys=True))
    except (ValueError,TypeError,OSError) as e:p.exit(1,"BLOCKED: "+str(e)+"\n")
if __name__=="__main__":main()
