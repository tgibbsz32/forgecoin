#!/usr/bin/env python3
"""Isolated dual FRG daemon loopback handshake smoke test, no mining.

Two separate clean LMDBs using the 20261026 build. No external network peers:
one node has --out-peers=0, the other an exclusive 127.0.0.1 peer.
Both P2P and RPC bind loopback; no blocks, payouts or pool service.
"""
import json
import pathlib
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

ROOT=pathlib.Path("/home/ubuntu/forgecoin-mainnet-20261026")
EXEC=ROOT/"build-release/bin/forged"
GENESIS="4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"
NONCE=20261026

def rest(port):
    url="http://127.0.0.1:{}/get_info".format(port)
    with urllib.request.urlopen(url,timeout=3) as response:
        return json.load(response)
def rpc(port,method,params=None):
    request=urllib.request.Request(
        "http://127.0.0.1:{}/json_rpc".format(port),
        data=json.dumps({"jsonrpc":"2.0","id":"p2p-qa","method":method,"params":params or {}}).encode(),
        headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(request,timeout=3) as response:
        data=json.load(response)
    if data.get("error"):
        raise AssertionError("RPC method rejected")
    return data["result"]

def stop(process):
    if process is None:return
    if process.poll() is None:
        process.terminate()
        try:process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill();process.wait(timeout=5)

def main():
    if not EXEC.is_file(): raise SystemExit("Pinned FRG daemon missing")
    qa=ROOT/"qa-pool-20261027"
    directory=pathlib.Path(tempfile.mkdtemp(prefix="duonode-loopback-",dir=qa))
    nodes=[]
    try:
        for number in (0,1):
            p2p=49580+number
            rpcport=49582+number
            commands=[str(EXEC),"--data-dir",str(directory/("chain"+str(number))),
              "--no-igd","--non-interactive","--hide-my-port","--allow-local-ip",
              "--p2p-bind-ip","127.0.0.1","--p2p-bind-port",str(p2p),
              "--rpc-bind-ip","127.0.0.1","--rpc-bind-port",str(rpcport),
              "--no-zmq","--check-updates","disabled","--disable-dns-checkpoints"]
            if number==0:
                commands+=["--out-peers","0","--in-peers","2"]
            else:
                commands+=["--out-peers","1","--in-peers","0",
                           "--add-exclusive-node","127.0.0.1:49580"]
            log=(directory/("node"+str(number)+".log")).open("w")
            process=subprocess.Popen(commands,stdin=subprocess.DEVNULL,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            nodes.append((process,log))
        deadline=time.monotonic()+33
        ok=False
        last=None
        while time.monotonic()<deadline:
            if any(proc.poll() is not None for proc,log in nodes):
                raise AssertionError("A QA node exited prematurely; inspect local QA logs")
            try:
                a,b=rest(49582),rest(49583)
                if a["height"]!=1 or b["height"]!=1:
                    raise AssertionError("Unexpected QA chain growth")
                if a.get("nettype")!="mainnet" or b.get("nettype")!="mainnet":
                    raise AssertionError("Network type changed")
                if (a.get("incoming_connections_count",0)>=1 and
                    b.get("outgoing_connections_count",0)>=1):
                    for port in (49582,49583):
                        genesis=rpc(port,"get_block_header_by_height",{"height":0})["block_header"]
                        if genesis["hash"]!=GENESIS or genesis["nonce"]!=NONCE:
                            raise AssertionError("Genesis mismatch")
                    last=(a,b)
                    ok=True
                    break
            except (urllib.error.URLError,ConnectionError,TimeoutError):
                pass
            time.sleep(.35)
        if not ok:
            raise AssertionError("Local-only P2P handshake not confirmed in bounded QA window")
        print(json.dumps({"status":"PASS_LOOPBACK_TWO_NODE_HANDSHAKE",
          "genesis":GENESIS,"nodeHeights":[a["height"],b["height"]],
          "nodeAIncoming":a.get("incoming_connections_count"),
          "nodeBOutgoing":b.get("outgoing_connections_count"),
          "allP2POnLoopback":True,"nodeAMaxOutgoing":0,
          "nodeBExclusivePeer":"127.0.0.1:49580",
          "minedBlocks":0,"publicMining":False,
          "walletRPC":False,"stratum":False,"logs":str(directory)},sort_keys=True))
    finally:
        for process,log in reversed(nodes):
            stop(process)
            log.close()
    if nodes and any(proc.poll() is None for proc,log in nodes):
        raise AssertionError("QA node still running")
    print("PASS: both loopback P2P processes terminated")

if __name__=="__main__":
    main()
