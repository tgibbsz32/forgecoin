"""INTEGRATION LAB ONLY: real disposable ForgeCoin daemon + two local XMRig.

The daemon is started with --offline in a NEW TemporaryDirectory and cannot
listen publicly; Stratum binds localhost only. The explicit offline wallet is
used solely to obtain a disposable public address. Zero mining rewards,
block submissions, ledger credits, or payouts are performed.

Never give production wallet/key paths, production node data directories,
mainnet/third-party pool endpoints or live pool credentials to this script.
Requires manually inspected local binaries; no downloads or auto-compilation.
"""
from argparse import ArgumentParser
import asyncio
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from services.pool_research.daemon_job_source import DaemonJobSource, LoopbackDaemonRpc
from services.pool_research.native_stratum_research import NativeResearchListener
from services.pool_research.persistent_randomx import PersistentRandomXAdapter

_B58 = r"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_ADDRESS_RE = re.compile(rf"(?<![{_B58}])[{_B58}]{{97}}(?![{_B58}])")


class TraceResearchListener(NativeResearchListener):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.job_sessions=set()
        self.native_by_session={}
        self.rejections={}

    async def send(self, writer, request_id, *, result=None, error=None):
        session=id(writer)
        if isinstance(result,dict) and "job" in result:
            self.job_sessions.add(session)
        if isinstance(result,dict) and result.get("status")=="POW_THRESHOLD_MET_UNCREDITED":
            self.native_by_session[session]=self.native_by_session.get(session,0)+1
        if error:
            m=str(error.get("message",""))[:100]
            self.rejections[m]=self.rejections.get(m,0)+1
        await super().send(writer, request_id,result=result,error=error)


async def run(args) -> None:
    for label in ("daemon_executable","wallet_cli_executable","xmrig_executable","native_worker",
                  "wallet_file","wallet_password_file"):
        p=Path(getattr(args,label)).resolve(strict=True)
        if not p.is_file():
            raise ValueError(f"{label}: existing regular file required")
    wallet=Path(args.wallet_file).resolve()
    if "disposable" not in wallet.name.lower():
        raise ValueError("only explicitly named disposable test wallets may be opened")
    wallet_keys=Path(str(wallet)+".keys")
    if not wallet_keys.is_file():
        raise ValueError("existing disposable wallet keys file required")
    env=os.environ.copy()
    if os.name=="nt":
        env["PATH"]=r"C:\msys64\mingw64\bin"+os.pathsep+env.get("PATH","")

    worker=None
    listener=None
    daemon=None
    miners=[]
    with tempfile.TemporaryDirectory(prefix="frg-two-xmrig-isolated-") as work:
        root=Path(work)
        wallet_copy=root/"disposable-wallet"
        shutil.copyfile(wallet,wallet_copy)
        shutil.copyfile(wallet_keys,Path(str(wallet_copy)+".keys"))
        pw_copy=root/"password.txt"
        shutil.copyfile(args.wallet_password_file,pw_copy)
        try:
            cli=subprocess.run([
                str(Path(args.wallet_cli_executable).resolve()),
                "--offline","--wallet-file",str(wallet_copy),
                "--password-file",str(pw_copy),"--command","address",
            ],env=env,capture_output=True,text=True,errors="replace",timeout=30)
            if cli.returncode:
                raise RuntimeError("disposable offline wallet address retrieval failed")
            addresses=set(_ADDRESS_RE.findall(cli.stdout))
            if len(addresses)!=1:
                raise RuntimeError("exactly one validated disposable wallet address required")
            address=addresses.pop()
            # This is an **isolated chain** using an otherwise mainnet-typed daemon.
            daemon_args=[
                str(Path(args.daemon_executable).resolve()),"--offline","--no-igd",
                "--data-dir",str(root/"empty-chain"),
                "--rpc-bind-ip","127.0.0.1","--rpc-bind-port","49881",
                "--p2p-bind-ip","127.0.0.1","--p2p-bind-port","49880",
                "--zmq-rpc-bind-ip","127.0.0.1","--zmq-rpc-bind-port","49882",
            ]
            with (root/"daemon.log").open("wb") as out:
                daemon=subprocess.Popen(daemon_args,stdin=subprocess.PIPE,
                    stdout=out,stderr=subprocess.STDOUT,env=env,
                    creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                rpc=LoopbackDaemonRpc("http://127.0.0.1:49881/json_rpc",timeout=2)
                info=None
                for _ in range(25):
                    if daemon.poll() is not None:
                        raise RuntimeError("disposable daemon exited before RPC readiness")
                    try:
                        info=await asyncio.to_thread(rpc,"get_info")
                        break
                    except (OSError,ValueError):
                        await asyncio.sleep(0.5)
                if info is None:
                    raise RuntimeError("offline disposable node never became ready")
                if (info.get("height") != 1 or info.get("offline") is not True
                        or info.get("synchronized") is not True):
                    raise RuntimeError("disposable empty-chain/offline assertions failed")
                genesis_result=await asyncio.to_thread(rpc,"get_block_header_by_height",{"height":0})
                genesis=genesis_result["block_header"]["hash"]
                nettype=info["nettype"]
                if nettype not in ("mainnet","testnet","stagenet"):
                    raise RuntimeError("daemon reported unsupported network type")
                # Same-daemon genesis lookup is NOT independent chain identity evidence.
                def factory():
                    return DaemonJobSource(rpc,expected_genesis_hash=genesis,
                        expected_nettype=nettype,wallet_address=address,
                        max_jobs=1,job_ttl=60)
                worker=PersistentRandomXAdapter(args.native_worker,timeout=15)
                listener=TraceResearchListener(
                    factory,worker,capacity=2,difficulty=args.difficulty,
                    idle_timeout=25,request_limit=64
                )
                port=await listener.start()
                xmrig=str(Path(args.xmrig_executable).resolve())
                for _ in range(2):
                    logfile=(root/f"xmrig-{len(miners)}.log").open("wb")
                    proc=subprocess.Popen([
                        xmrig,"--url",f"127.0.0.1:{port}","--user","DISPOSABLE_LOCAL_ONLY",
                        "--pass","x","--algo","rx/0","--threads","1",
                        "--randomx-mode","light","--donate-level","0",
                        "--no-color","--randomx-wrmsr=-1",
                    ],env=env,stdin=subprocess.DEVNULL,stdout=logfile,
                      stderr=subprocess.STDOUT,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                    miners.append((proc,logfile))
                await asyncio.sleep(args.seconds)
                for proc,_ in miners:
                    if proc.poll() is not None:
                        raise RuntimeError("a miner exited before the bounded test interval")
                summary={
                    "empty_chain_height":info["height"],
                    "job_sessions":len(listener.job_sessions),
                    "sessions_with_native_verified_shares":sum(
                        1 for n in listener.native_by_session.values() if n>0),
                    "verified_share_count":sum(listener.native_by_session.values()),
                    "rejections":listener.rejections,
                }
                print("DISPOSABLE_DAEMON_XMRIG_OBSERVATION",summary)
                if len(listener.job_sessions)!=2:
                    raise AssertionError("both XMRig clients must receive independent real-daemon jobs")
                if summary["sessions_with_native_verified_shares"] != 2:
                    raise AssertionError("both XMRig clients must independently submit a native-verified share")
                print("PASS: TWO XMRig clients independently verified native real-daemon jobs")
                print("NOT PROVEN: accepted blocks, fully independent chain identity or mining payouts")
        finally:
            for proc, log in miners:
                try:
                    if proc.poll() is None:
                        proc.terminate()
                        try:await asyncio.to_thread(proc.wait,timeout=5)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            await asyncio.to_thread(proc.wait,timeout=5)
                finally:
                    log.close()
            if listener is not None:
                await listener.close()
            if worker is not None:
                worker.close()
            if daemon is not None:
                if daemon.poll() is None:
                    try:
                        daemon.stdin.write(b"exit\n")
                        daemon.stdin.flush()
                        await asyncio.to_thread(daemon.wait,timeout=6)
                    except (OSError,subprocess.TimeoutExpired):
                        daemon.kill()
                        await asyncio.to_thread(daemon.wait,timeout=5)
                print("DISPOSABLE_DAEMON_STOPPED",daemon.poll() is not None)


if __name__=="__main__":
    p=ArgumentParser(description=__doc__)
    p.add_argument("--daemon-executable",required=True)
    p.add_argument("--wallet-cli-executable",required=True)
    p.add_argument("--wallet-file",required=True)
    p.add_argument("--wallet-password-file",required=True)
    p.add_argument("--xmrig-executable",required=True)
    p.add_argument("--native-worker",required=True)
    p.add_argument("--seconds",type=int,default=24)
    p.add_argument("--difficulty",type=int,default=30)
    a=p.parse_args()
    if not 5<=a.seconds<=35 or not 1<=a.difficulty<=0xffffffff:
        p.error("bounded mining duration/difficulty invalid")
    asyncio.run(run(a))
