#!/usr/bin/env python3
"""Read-only check of privately mined FRG block 1 from disposable Windows QA.

No mining, no public peers, no wallet secrets. Restarts one local daemon,
verifies persisted accepted block at real consensus difficulty, then stops.
"""
import hashlib
import json
import pathlib
import subprocess
import time
import sys
import urllib.error
import urllib.request

BASE=pathlib.Path.home()/"Documents/Codex/2026-10-27/ForgeCoin-LOCAL-FULL-BLOCK-QA/isolated-block-qa-4eqsd_rg"
NODE=BASE/("node-1" if "--peer" in sys.argv else "node-0")
DAEMON=pathlib.Path.home()/"Downloads/ForgeCoin-Mainnet-20261026-Prelaunch-Wallet-v0.4/bin/forged.exe"
REPO=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=json.loads((REPO/"config/mainnet.identity.json").read_text())
GENESIS=MANIFEST["genesis_hash"]
MINED="9755a4f129f97b7865e5897e79abf5fea89dec2ba776d53fb9d01942b9f7ba9e"

def rpc(method,params):
    req=urllib.request.Request("http://127.0.0.1:%d/json_rpc"%(49783 if "--peer" in sys.argv else 49782),
       data=json.dumps({"jsonrpc":"2.0","id":"inspect","method":method,"params":params}).encode(),
       headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=4) as res:
        data=json.load(res)
    if data.get("error"):raise AssertionError("QA RPC error")
    return data["result"]

def main():
    assert NODE.is_dir() and DAEMON.is_file(),"disposable mining chain or daemon missing"
    with DAEMON.open("rb") as stream:
        assert hashlib.file_digest(stream,"sha256").hexdigest()==MANIFEST["windows_prelaunch_binaries_sha256"]["forged.exe"]
    args=[str(DAEMON),"--offline","--data-dir",str(NODE),"--non-interactive",
       "--p2p-bind-ip","127.0.0.1","--p2p-bind-port",("49781" if "--peer" in sys.argv else "49780"),
       "--rpc-bind-ip","127.0.0.1","--rpc-bind-port",("49783" if "--peer" in sys.argv else "49782"),"--no-igd",
       "--no-zmq","--check-updates","disabled","--disable-dns-checkpoints"]
    proc=None
    with (BASE/"read-only-block-inspect.log").open("w") as log:
        try:
            proc=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW)
            end=time.monotonic()+20
            while time.monotonic()<end:
                try:
                    genesis=rpc("get_block_header_by_height",{"height":0})["block_header"]
                    block=rpc("get_block_header_by_height",{"height":1})["block_header"]
                    break
                except (OSError,TimeoutError,urllib.error.URLError,KeyError,ValueError):
                    time.sleep(.3)
            else:raise AssertionError("QA offline node did not return stored block")
            assert genesis["hash"]==GENESIS and genesis["nonce"]==20261026
            assert block["hash"]==MINED and block["height"]==1
            assert int(block["difficulty"])==500000, "QA must use frozen mainnet consensus difficulty"
            assert int(block["reward"])==2384185222
            assert block["orphan_status"] is False
            assert block["prev_hash"]==GENESIS
            body=rpc("get_block",{"height":1})
            assert body["block_header"]["hash"]==MINED
            # Exercise real read-only daemon HTTP paths used by the new
            # payout canonicality verifier (no wallet RPC required).
            import sys
            sys.path.insert(0,str(REPO))
            from services.pool_settlement.verify_rpc import ReadOnlyRPCVerifier
            observer=ReadOnlyRPCVerifier("http://127.0.0.1:49782",
                                         "http://127.0.0.1:49783")
            assert observer.identity()==1, "read-only payout observer rejected actual QA node"
            print("PASS_READONLY_PAYOUT_VERIFIER_AGAINST_REAL_FRG_DAEMON_GENESIS_AND_TIP",flush=True)
            print(json.dumps({"status":"PASS_STORED_NATIVE_FULL_BLOCK_REAL_CONSENSUS",
                "genesisHash":GENESIS,"block1Hash":MINED,
                "minedAtDifficulty":block["difficulty"],"rewardAtomic":block["reward"],
                "orphaned":False,"previousHash":block["prev_hash"],
                "publicPeers":0,"publicMiningActive":False,
                "qaOnly":True},sort_keys=True),flush=True)
        finally:
            if proc is not None:
                if proc.poll() is None:
                    proc.terminate()
                    try:proc.wait(timeout=8)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=4)
                print("PASS: temporary read-only daemon stopped",flush=True)

if __name__=="__main__":main()
