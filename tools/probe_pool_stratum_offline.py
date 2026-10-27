#!/usr/bin/env python3
"""Offline local-only native Stratum acceptance/rejection QA.

NO valid hash is computed; only login/job and intentionally invalid share.
Never connects to a public pool, never mines or submits an actual block.
"""
import json
import pathlib
import socket
import urllib.request
import re
base=pathlib.Path("/home/ubuntu/forgecoin-mainnet-20261026")
address=(base/"qa-wallet-20261027/public-qa-only-address.txt").read_text().strip()
genesis="4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"

def recv_json(sock):
    b=b""
    while len(b)<200000:
        x=sock.recv(4096)
        if not x:break
        b+=x
        if b"\n" in b:break
    return json.loads(b.split(b"\n")[0])
with socket.create_connection(("127.0.0.1",49442),timeout=6) as sock:
    sock.settimeout(8)
    payload={"id":1,"jsonrpc":"2.0","method":"login",
             "params":{"login":address,"pass":"qa-not-real","agent":"forgecoin-offline-integration"}}
    sock.sendall((json.dumps(payload,separators=(",",":"))+"\n").encode())
    ans=recv_json(sock)
    if not isinstance(ans,dict) or not isinstance(ans.get("result"),dict):
        raise AssertionError("No job on authenticated address login (error="+str(ans.get("error") if isinstance(ans,dict) else None)+")")
    res=ans["result"]
    job=res.get("job")
    if not isinstance(job,dict):
        raise AssertionError("Native C pool login returned no RandomX job")
    assert job.get("height")==1, "Expected disposable height-one block template"
    assert job.get("seed_hash")==genesis, "Wrong RandomX seed/genesis"
    assert isinstance(job.get("blob"),str) and len(job["blob"])>70
    assert re.fullmatch(r"[0-9a-fA-F]{8,16}",job.get("target",""))
    assert re.fullmatch(r"[0-9a-fA-F]{32}",job.get("job_id",""))
    assert isinstance(res.get("id"),str) and len(res["id"])==32
    print(json.dumps({"status":"QA_NATIVE_STRATUM_LOGIN_AND_JOB_PASS",
       "height":job["height"],"seedHashMatches":True,
       "blobHexCharacters":len(job["blob"]),
       "targetHex":job.get("target"),"payoutAddress":"disposable QA only",
       "note":"No share or block has been mined"},sort_keys=True))
    invalid={"id":2,"jsonrpc":"2.0","method":"submit",
             "params":{"id":res["id"],"job_id":job["job_id"],
                       "nonce":"zzzzzzzz","result":"0"*64}}
    sock.sendall((json.dumps(invalid,separators=(",",":"))+"\n").encode())
    ans2=recv_json(sock)
    error=ans2.get("error") if isinstance(ans2,dict) else None
    if not error:
        raise AssertionError("Malformed mining share was NOT rejected")
    print("QA_INVALID_SHARE_REJECTED: true; response category:",str(error)[:140])
    # Exercise native RandomX verification using a syntactically valid nonce
    # and a deliberately false digest. This is never a mined share.
    fake={"id":3,"jsonrpc":"2.0","method":"submit",
          "params":{"id":res["id"],"job_id":job["job_id"],
                    "nonce":"00000000","result":"0"*64}}
    sock.sendall((json.dumps(fake,separators=(",",":"))+"\n").encode())
    fake_reply=recv_json(sock)
    fake_error=fake_reply.get("error") if isinstance(fake_reply,dict) else None
    if not fake_error:
        raise AssertionError("Incorrect RandomX digest was not rejected!")
    print("QA_INCORRECT_RANDOMX_DIGEST_REJECTED: true; category:",str(fake_error)[:140])
with urllib.request.urlopen("http://127.0.0.1:49443/stats",timeout=3) as response:
    stats=json.load(response)
print("QA_NATIVE_POOL_STATS:",json.dumps({
    k:stats.get(k) for k in ("pool_hashrate","connected_miners","pool_blocks_found","round_hashes",
                             "network_height","network_difficulty","pool_fee","pool_port")},sort_keys=True))
assert stats.get("pool_blocks_found")==0, "Unexpected block! Abort and investigate"
