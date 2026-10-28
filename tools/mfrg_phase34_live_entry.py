#!/usr/bin/env python3
"""Owner-intake to opt-in read-only Solana RPC inventory bridge.

Default is strictly offline. Live requires explicit --live and two distinct
operator-selected RPC origins. Returns NO custody, sales, or release authority.
"""
import argparse
import json
import sys
from urllib.parse import urlsplit
from mfrg_owner_deployment_intake import validate as validate_intake
from read_mfrg_mainnet_inventory import assess as assess_inventory

class PhaseEntryError(ValueError):pass

def build(record, rpc_one=None, rpc_two=None, live=False, rpc=None):
    intake=validate_intake(record)
    result={"phase":"LIVE_MAINNET_PROVENANCE_EVIDENCE_INTAKE",
            "intake":intake,"live_reads_performed":False,
            "mainnet_mint_ownership_authenticated":False,
            "issuer_and_treasury_control_authenticated":False,
            "token_operations_authorized":False}
    if not live:
        result["status"]="PREFLIGHT_ONLY_LIVE_EVIDENCE_NOT_COLLECTED"
        return result
    if not (isinstance(rpc_one,str) and isinstance(rpc_two,str)):
        raise PhaseEntryError("two explicitly configured RPC origins required")
    from read_mfrg_mainnet_provenance import exact_https_origin
    one=exact_https_origin(rpc_one);two=exact_https_origin(rpc_two)
    if one==two:raise PhaseEntryError("distinct RPC origins required")
    if urlsplit(one).hostname==urlsplit(two).hostname:
        raise PhaseEntryError("distinct RPC hostnames required")
    params={"rpc":rpc} if rpc is not None else {}
    inventory=assess_inventory(record["mint"],record["initialization_signature"],one,two,**params)
    result["status"]="LIVE_RPC_CONSISTENCY_NOT_CUSTODY_AUTHENTICATION"
    result["live_reads_performed"]=True
    result["inventory"]=inventory
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_intake_json")
    p.add_argument("--live",action="store_true",help="explicitly enable read-only mainnet RPC calls")
    p.add_argument("--rpc-one")
    p.add_argument("--rpc-two")
    a=p.parse_args()
    try:
        with open(a.owner_intake_json,encoding="utf-8") as file:record=json.load(file)
        report=build(record,a.rpc_one,a.rpc_two,a.live)
        print(json.dumps(report,sort_keys=True,indent=2))
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print(json.dumps({"status":"BLOCKED","error":str(exc),"token_operations_authorized":False}),file=sys.stderr)
        return 2
    return 0
if __name__=="__main__":raise SystemExit(main())
