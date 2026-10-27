#!/usr/bin/env python3
"""Strictly read-only template sanity check against the *offline* frozen mainnet QA node.

Never calls start_mining, submit_block, a wallet RPC, a pool or a payout method.
Not proof of RandomX share acceptance and not public launch authorization.
"""
import json
import pathlib
import urllib.request

MANIFEST = pathlib.Path(__file__).resolve().parents[1] / "config" / "mainnet.identity.json"
RPC = "http://127.0.0.1:39481/json_rpc"

def rpc(method, params=None):
    if method not in {"get_info", "get_block_header_by_height", "get_block_template"}:
        raise ValueError("disallowed RPC method")
    data = json.dumps({"jsonrpc":"2.0","id":"read-only-qa","method":method,
                       "params":params or {}}).encode()
    req = urllib.request.Request(RPC,data=data,method="POST",headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=5) as response:
        raw = response.read(262144)
    result = json.loads(raw)
    if result.get("error"):
        raise RuntimeError(f"RPC {method} error: {result['error']}")
    return result["result"]

def main():
    conf=json.loads(MANIFEST.read_text(encoding="utf-8"))
    if conf["release_authorized"] is not False or conf["stage"] != "genesis-frozen":
        raise RuntimeError("This probe only runs before launch")
    info=rpc("get_info")
    genesis=rpc("get_block_header_by_height",{"height":0})["block_header"]
    assert info["nettype"]=="mainnet" and info["height"]==1
    assert genesis["hash"]==conf["genesis_hash"] and genesis["nonce"]==20261026
    reward_address=conf["pool"]["operator_fee_address"]
    assert isinstance(reward_address,str) and len(reward_address)>90
    template=rpc("get_block_template",{"wallet_address":reward_address,"reserve_size":8})
    blob=template.get("blocktemplate_blob")
    assert isinstance(blob,str) and len(blob)>120 and len(blob)%2==0
    assert int(template.get("height",-1))==1
    assert int(template.get("difficulty",-1))==500000
    assert 0 <= int(template.get("reserved_offset",-1)) < len(blob)//2
    print(json.dumps({"status":"template-generated-without-mining",
                      "network":conf["chain"],
                      "height":template["height"],
                      "difficulty":template["difficulty"],
                      "expected_reward_atomic":template.get("expected_reward"),
                      "seed_hash_present":bool(template.get("seed_hash")),
                      "blob_length_bytes":len(blob)//2,
                      "genesis_hash":genesis["hash"],
                      "launch_authorized":False},indent=2))

if __name__=="__main__":
    main()
