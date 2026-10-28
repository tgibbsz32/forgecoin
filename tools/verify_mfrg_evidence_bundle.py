#!/usr/bin/env python3
"""Step 25: offline immutable evidence-bundle integrity and recovery manifest checks.

No RPC, trusted chain proof, signer custody proof, or production authorization.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

class EvidenceError(ValueError): pass
def need(condition, why):
    if not condition: raise EvidenceError(why)
def digest(data): return hashlib.sha256(data).hexdigest()
def validate(bundle, files):
    need(isinstance(bundle,dict) and set(bundle)=={"version","network","mint","initialization_signature","sources","artifacts","backup"}, "bundle schema")
    need(type(bundle["version"]) is int and bundle["version"]==1 and bundle["network"]=="solana-mainnet-beta","version/network")
    need(isinstance(bundle["mint"],str) and 32<=len(bundle["mint"])<=44 and bundle["mint"]!="9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw","real mainnet mint identifier required, devnet forbidden")
    need(isinstance(bundle["initialization_signature"],str) and len(bundle["initialization_signature"])>=64,"initialization signature required")
    sources=bundle["sources"]
    need(isinstance(sources,list) and len(sources)>=2,"at least two declared sources")
    ids=set(); origins=set()
    for s in sources:
        need(isinstance(s,dict) and set(s)=={"id","origin","slot","commitment","artifact"},"source fields")
        need(isinstance(s["id"],str) and s["id"] not in ids,"duplicate source id")
        need(isinstance(s["origin"],str) and s["origin"].startswith("https://") and s["origin"] not in origins,"distinct HTTPS origins required")
        need(type(s["slot"]) is int and s["slot"]>0 and s["commitment"]=="finalized","finalized slot required")
        ids.add(s["id"]);origins.add(s["origin"])
    artifacts=bundle["artifacts"]
    need(isinstance(artifacts,dict) and artifacts,"artifacts required")
    need(set(files)==set(artifacts),"artifact set mismatch")
    for name, expected in artifacts.items():
        need(isinstance(name,str) and re.fullmatch(r"[a-zA-Z0-9_.-]+",name) and name not in (".",".."),"unsafe artifact name")
        need(isinstance(expected,str) and re.fullmatch("[a-f0-9]{64}",expected) is not None,"invalid SHA256")
        need(digest(files[name])==expected,f"artifact digest mismatch: {name}")
    need(all(s["artifact"] in artifacts for s in sources),"missing source artifact")
    backup=bundle["backup"]
    need(isinstance(backup,dict) and set(backup)=={"sha256","size_bytes","snapshot_file"},"backup metadata")
    need(backup["snapshot_file"] in artifacts,"backup artifact missing")
    need(type(backup["size_bytes"]) is int and backup["size_bytes"]==len(files[backup["snapshot_file"]]),"backup size mismatch")
    need(backup["sha256"]==artifacts[backup["snapshot_file"]],"backup checksum mismatch")
    return {"status":"OFFLINE_INTEGRITY_ONLY_NOT_CHAIN_PROOF","artifacts_checked":len(artifacts),
            "sources_declared":len(sources),"provider_independence_verified":False,
            "external_evidence_authenticated":False,"backup_restore_tested":False,
            "mint_authenticated":False,"sale_authorized":False,"treasury_release_authorized":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("bundle_json");p.add_argument("artifact_directory")
    a=p.parse_args()
    try:
        root=pathlib.Path(a.artifact_directory).resolve()
        with open(a.bundle_json,encoding="utf8") as f:b=json.load(f)
        need(isinstance(b.get("artifacts"),dict),"artifacts mapping required")
        files={}
        for name in b["artifacts"]:
            need(isinstance(name,str) and re.fullmatch("[a-zA-Z0-9_.-]+",name) and name not in (".",".."),"unsafe filename")
            path=root/name
            need(path.is_file() and not path.is_symlink(),"missing or symlinked file")
            need(path.stat().st_size<=16*1024*1024,"artifact oversized")
            files[name]=path.read_bytes()
        print(json.dumps(validate(b,files),indent=2,sort_keys=True))
    except (OSError,ValueError,TypeError,KeyError) as ex:
        print("BLOCKED: "+str(ex),file=sys.stderr);return 1
    return 0
if __name__=="__main__":raise SystemExit(main())
