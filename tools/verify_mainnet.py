#!/usr/bin/env python3
"""Read-only fail-closed ForgeCoin mainnet identity preflight.

No mining, block submission, wallet authentication, or chain changes.
Does not grant launch approval. Never accepts an absent genesis hash for launch.
"""
import argparse
import json
import pathlib
import urllib.request
import urllib.parse
import sys

MANIFEST = pathlib.Path(__file__).resolve().parents[1] / "config/mainnet.identity.json"

def rpc(url, method, params):
    request = urllib.request.Request(
        url.rstrip("/") + "/json_rpc",
        json.dumps({"jsonrpc":"2.0","id":"fresh-mainnet-preflight","method":method,"params":params}).encode(),
        headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=4) as response:
        result = json.load(response)
    if result.get("error") or result.get("result", {}).get("status") not in ("OK", None):
        raise RuntimeError("RPC rejected " + method)
    return result["result"]

def audit(manifest, state, genesis, *, require_genesis_only=True, require_launch_hash=True):
    if manifest.get("stage") not in ("prelaunch-genesis-only", "genesis-frozen", "launched"):
        raise ValueError("Unknown release stage")
    if int(genesis.get("height", -1)) != 0:
        raise ValueError("Wrong genesis height")
    if int(genesis.get("nonce", -1)) != manifest["genesis_nonce"]:
        raise ValueError("Genesis nonce mismatch: wrong blockchain")
    if state.get("nettype") != "mainnet":
        raise ValueError("Daemon is not in mainnet mode")
    if require_genesis_only and int(state.get("height", -1)) != 1:
        raise ValueError("Chain has mined blocks or missing genesis: do not reuse for clean launch")
    actual_hash = genesis.get("hash")
    if not isinstance(actual_hash, str) or len(actual_hash) != 64:
        raise ValueError("Missing genesis hash")
    expected = manifest.get("genesis_hash")
    if require_launch_hash and not expected:
        raise ValueError("Official genesis hash not frozen: no launch authorization")
    if expected and expected.lower() != actual_hash.lower():
        raise ValueError("Genesis hash mismatch: refusing old or substituted chain")
    return {"chain":manifest["chain"],"genesis_nonce":genesis["nonce"],
            "genesis_hash":actual_hash,"height":state["height"],
            "identity_matches_nonce":True,"genesis_hash_frozen":bool(expected),
            "launch_authorized":bool(manifest.get("release_authorized"))}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc-url",default="http://127.0.0.1:39481")
    parser.add_argument("--allow-unfrozen-prelaunch",action="store_true",
                        help="For isolated genesis inspection only; NEVER authorizes launch.")
    parser.add_argument("--allow-mined-chain",action="store_true",
                        help="For diagnostics on a previously launched chain ONLY.")
    args=parser.parse_args()
    u=urllib.parse.urlsplit(args.rpc_url)
    if (u.scheme != "http" or u.hostname not in ("127.0.0.1", "::1")
        or u.username or u.password or u.query or u.fragment or u.path not in ("","/")
        or u.port != 39481):
        parser.error("Read-only preflight permits only http://127.0.0.1:39481")
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    state=rpc(args.rpc_url,"get_info",{})
    genesis=rpc(args.rpc_url,"get_block_header_by_height",{"height":0})["block_header"]
    report=audit(manifest,state,genesis,
                 require_genesis_only=not args.allow_mined_chain,
                 require_launch_hash=not args.allow_unfrozen_prelaunch)
    print(json.dumps(report,indent=2))
    if not report["genesis_hash_frozen"]:
        print("UNFROZEN GENESIS: prelaunch inspection only; DO NOT MINE",file=sys.stderr)
        return 2
    return 0

if __name__=="__main__":
    try: sys.exit(main())
    except (OSError,ValueError,RuntimeError,KeyError) as exc:
        print("FAIL CLOSED:",str(exc),file=sys.stderr)
        sys.exit(1)
