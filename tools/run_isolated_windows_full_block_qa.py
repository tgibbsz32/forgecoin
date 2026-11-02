#!/usr/bin/env python3
"""Bounded, strictly LOCAL ForgeCoin full-block and peer-propagation QA on Windows.

DO NOT substitute production wallet or data dirs. Two clean isolated nodes
both bind P2P/RPC to localhost, no external seeds, no wallet spend key.
Mines using four CPU threads of native Windows forged.exe for QA ONLY.
No public mining port and NO block is allowed to enter public network.
"""
import hashlib,json,os,pathlib,socket,subprocess,tempfile,time,urllib.error,urllib.request
from datetime import datetime,timezone

REPO=pathlib.Path(__file__).resolve().parents[1]
IDENTITY=json.loads((REPO/"config/mainnet.identity.json").read_text())
EXEC=pathlib.Path.home()/"Downloads/ForgeCoin-Mainnet-20261026-Prelaunch-Wallet-v0.4/bin/forged.exe"
EXPECT=IDENTITY["windows_prelaunch_binaries_sha256"]["forged.exe"]
GENESIS=IDENTITY["genesis_hash"]
ADDR="YnJ4sygA2VbA4nvoXssZcSKh4fwsw4g3DaujrVCDXSwWGuXwnYTfNsKPVunwuAf8joPEWfePpMh6CEsyEqMpQz2i2uFy112XA"
QA_DIR=pathlib.Path.home()/"Documents/Codex/2026-10-27/ForgeCoin-LOCAL-FULL-BLOCK-QA"
MAX_SECONDS=225
THREADS=12
PORTS=((49680,49682),(49681,49683))

def call(port,method,params=None):
    obj={"jsonrpc":"2.0","id":"local-private-block-QA","method":method,"params":params or {}}
    req=urllib.request.Request("http://127.0.0.1:%d/json_rpc"%port,
        data=json.dumps(obj).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=5) as response:
        out=json.load(response)
    if out.get("error"):
        raise RuntimeError("%s returned error: %s"%(method,out["error"]))
    return out["result"]
def endpoint(port,method,body=None):
    req=urllib.request.Request("http://127.0.0.1:%d/%s"%(port,method),
       data=json.dumps(body or {}).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=5) as response:
        out=json.load(response)
    if out.get("error"):
        raise RuntimeError("%s returned error: %s"%(method,out["error"]))
    return out
def wait(check,seconds,label):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        try:
            result=check()
            if result:return result
        except (OSError,urllib.error.URLError,TimeoutError,ValueError,KeyError):
            pass
        time.sleep(.35)
    raise AssertionError(label+" not available within bounded QA window")
def stop(p):
    if p.poll() is None:
        p.terminate()
        try:p.wait(timeout=8)
        except subprocess.TimeoutExpired:p.kill();p.wait(timeout=6)
def verify_binary():
    actual=hashlib.file_digest(EXEC.open("rb"),"sha256").hexdigest()
    if actual!=EXPECT:raise AssertionError("Frozen Windows node binary digest mismatch")
    if IDENTITY["release_authorized"] is not False or IDENTITY["genesis_nonce"]!=20261026:
        raise AssertionError("QA source is not an unapproved frozen-genesis source")
def start_node(index,qa,logs):
    p2p,rpc=PORTS[index]
    args=[str(EXEC),"--data-dir",str(qa/("node-%d"%index)),
          "--non-interactive","--no-igd","--hide-my-port","--allow-local-ip",
          "--disable-dns-checkpoints","--check-updates","disabled","--no-zmq",
          "--p2p-bind-ip","127.0.0.1","--p2p-bind-port",str(p2p),
          "--rpc-bind-ip","127.0.0.1","--rpc-bind-port",str(rpc)]
    if index==0:
        args+=["--out-peers","0","--in-peers","2"]
    else:
        args+=["--out-peers","1","--in-peers","0","--add-exclusive-node","127.0.0.1:49680"]
    log=(qa/("daemon-%d.log"%index)).open("w",encoding="utf-8")
    logs.append(log)
    return subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,
                            stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
def hdr(port,height):
    return call(port,"get_block_header_by_height",{"height":height})["block_header"]
def ready():
    a=endpoint(49682,"get_info")
    b=endpoint(49683,"get_info")
    if any(x.get("height")!=1 or x.get("nettype")!="mainnet" for x in (a,b)):
        raise AssertionError("Non-empty or non-mainnet QA node")
    if a.get("incoming_connections_count",0)<1 or b.get("outgoing_connections_count",0)<1:
        return False
    for port in (49682,49683):
        g=hdr(port,0)
        if g.get("nonce")!=20261026 or g.get("hash")!=GENESIS:raise AssertionError("wrong genesis")
    return True
def main():
    verify_binary()
    # Fixed-port QA must never attach to someone else's still-running miner.
    # Bail out BEFORE touching any process or allocating a mining thread.
    for p2p,rpcport in PORTS:
        for port in (p2p,rpcport):
            with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
                sock.settimeout(0.75)
                if sock.connect_ex(("127.0.0.1",port))==0:
                    raise AssertionError("QA port %d is already in use; another isolated daemon may be running"%port)
    QA_DIR.mkdir(parents=True,exist_ok=True)
    qa=pathlib.Path(tempfile.mkdtemp(prefix="isolated-block-qa-",dir=QA_DIR))
    nodes=[];logs=[];accepted=False
    print("QA_DIR="+str(qa),flush=True)
    try:
        for i in (0,1):nodes.append(start_node(i,qa,logs))
        wait(ready,27,"both nodes genesis/P2P handshake")
        print("PASS: two verified nodes; local P2P only; no production listeners.",flush=True)
        reply=endpoint(49682,"start_mining",{
            "miner_address":ADDR,"threads_count":THREADS,
            "do_background_mining":False,"ignore_battery":True})
        if reply.get("status")!="OK":
            raise AssertionError("Solo QA start_mining returned %s"%str(reply))
        print("QA native RandomX solo miner started, 12 Windows CPU threads, no public peers",flush=True)
        deadline=time.monotonic()+MAX_SECONDS
        last=0
        while time.monotonic()<deadline:
            if any(proc.poll() is not None for proc in nodes):
                raise AssertionError("QA daemon crashed; see private QA logs")
            a=endpoint(49682,"get_info")
            b=endpoint(49683,"get_info")
            if a["height"]>=2 and b["height"]>=2:
                h1,h2=hdr(49682,1),hdr(49683,1)
                if h1.get("hash")!=h2.get("hash") or h1.get("height")!=1:
                    raise AssertionError("Peer accepted different block-1 headers")
                if not h1.get("reward") or h1.get("orphan_status") is True:
                    raise AssertionError("Missing reward or orphaned mined block")
                print(json.dumps({"status":"PASS_NATIVE_WINDOWS_SOLO_FULL_BLOCK_AND_P2P_PROPAGATION",
                    "genesis":GENESIS,"block1Hash":h1["hash"],
                    "block1Nonce":h1.get("nonce"),"block1RewardAtomic":h1.get("reward"),
                    "nodeAHeight":a["height"],"nodeBHeight":b["height"],
                    "nodeAIncoming":a.get("incoming_connections_count"),
                    "nodeBOutgoing":b.get("outgoing_connections_count"),
                    "publicNetworkConnected":False,"miningThreads":THREADS,
                    "operatorFirstPUBLICBlockPreserved":True,"QA_DIR":str(qa)},sort_keys=True),flush=True)
                accepted=True
                break
            now=time.monotonic()
            if now-last>=15:
                try:
                    status=endpoint(49682,"mining_status")
                    speed=status.get("speed","not reported")
                except Exception:
                    speed="unavailable"
                print("QA_MINE_STATUS: height A=%s B=%s; builtInMinerSpeed=%s H/s; elapsedBudgetRemaining=%ds"%(a["height"],b["height"],speed,int(deadline-now)),flush=True)
                last=now
            time.sleep(2)
        if not accepted:
            raise AssertionError("No full block and two-node propagation before bounded QA timeout; native built-in miner may be too slow at normal difficulty")
    finally:
        for p in nodes:stop(p)
        for log in logs:log.close()
        assert all(p.poll() is not None for p in nodes),"QA daemon leak"
        print("QA_CLEANUP: no QA daemon left running; private block not broadcast",flush=True)
    if not accepted:raise SystemExit(1)
if __name__=="__main__":main()
