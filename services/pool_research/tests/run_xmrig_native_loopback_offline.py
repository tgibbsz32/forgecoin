"""One-shot bounded XMRig interoperability probe against a fake daemon.

NEVER points XMRig at a real chain, pool, address or third-party endpoint.
No persisted shares, payouts, mining revenues, submit_block or wallet keys.
Requires explicit reviewed XMRig + native RandomX helper paths. Light mode,
single thread, loopback-only and strict wall-clock timeout are mandatory.
"""
import argparse
import asyncio
import os
from pathlib import Path
import subprocess
import tempfile

from services.pool_research.daemon_job_source import DaemonJobSource
from services.pool_research.native_stratum_research import NativeResearchListener
from services.pool_research.persistent_randomx import PersistentRandomXAdapter
from services.pool_research.test_daemon_job_source import FakeDaemon, GENESIS

class InstrumentedListener(NativeResearchListener):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.events=[]
    async def send(self,writer,request_id,*,result=None,error=None):
        if error:
            self.events.append(("ERROR",str(error.get("message",""))[:100]))
        elif isinstance(result,dict) and "job" in result:
            self.events.append(("LOGIN",str(result.get("status",""))))
        elif isinstance(result,dict) and "status" in result:
            self.events.append(("SUBMIT_OR_KEEPALIVE",str(result["status"])))
        return await super().send(writer,request_id,result=result,error=error)


async def main(args):
    exe=Path(args.xmrig_executable).resolve(strict=True)
    native_exe=Path(args.native_worker).resolve(strict=True)
    if not exe.is_file() or not native_exe.is_file() or exe == native_exe:
        raise ValueError("two explicit distinct native executable files required")
    fake=FakeDaemon()
    def factory():
        return DaemonJobSource(
            fake,expected_genesis_hash=GENESIS,expected_nettype="testnet",
            wallet_address="DISPOSABLE_TEST_ADDRESS",max_jobs=1,job_ttl=60,
        )
    worker=PersistentRandomXAdapter(native_exe,timeout=10)
    listener=InstrumentedListener(factory,worker,difficulty=1,idle_timeout=25,request_limit=64)
    process=None
    try:
        port=await listener.start()
        with tempfile.TemporaryDirectory(prefix="forgecoin-xmrig-isolated-") as root:
            output=Path(root)/"xmrig.log"
            cmd=[
                str(exe),"--url",f"127.0.0.1:{port}",
                "--user","DISPOSABLE_OFFLINE_XMRIG",
                "--pass","x","--algo","rx/0",
                "--threads","1","--randomx-mode","light",
                "--donate-level","0","--no-color",
                "--print-time","5",
                "--randomx-wrmsr=-1",
            ]
            with output.open("wb") as f:
                process=subprocess.Popen(
                    cmd,stdin=subprocess.DEVNULL,stdout=f,
                    stderr=subprocess.STDOUT,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0)
                )
                await asyncio.sleep(args.seconds)
                exited_early = process.poll() is not None
                if not exited_early:
                    process.terminate()
                    try:await asyncio.to_thread(process.wait,timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        await asyncio.to_thread(process.wait,timeout=5)
            text=output.read_text(encoding="utf-8",errors="replace")
            print("OFFLINE_XMRIG_EXIT",process.returncode)
            print("LOCAL_LISTENER_EVENTS",listener.events[:30])
            print("MINER_LOG_START",repr(text[:1500]))
            print("MINER_LOG_END",repr(text[-2500:]))
            print("NETWORK_BOUND",f"127.0.0.1:{port}")
            if process.returncode not in (0,1,2,3221225786,3221225781):
                print("MINER_EXIT_NONSTANDARD",process.returncode)
            if "unknown option" in text.lower() or exited_early:
                raise AssertionError("XMRig exited before the bounded research interval")
            if not any(e[0]=="LOGIN" for e in listener.events):
                raise AssertionError("XMRig did not receive a daemon-bound job")
            verified = sum(e == ("SUBMIT_OR_KEEPALIVE", "POW_THRESHOLD_MET_UNCREDITED")
                           for e in listener.events)
            print("NATIVE_VERIFIED_XMRIG_SUBMISSIONS", verified)
            if verified < 1:
                raise AssertionError("no genuine XMRig share passed native RandomX verification")
            print("PASS: actual XMRig login AND native RandomX digest-matched submissions")
            print("NOTICE: test daemon fixture, no live block, share credit or payout")
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            await asyncio.to_thread(process.wait,timeout=5)
        await listener.close()
        worker.close()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xmrig-executable",required=True)
    p.add_argument("--native-worker",required=True)
    p.add_argument("--seconds",type=int,default=24)
    a=p.parse_args()
    if not 5 <= a.seconds <= 45:
        raise SystemExit("bounded test time must be 5..45 seconds")
    asyncio.run(main(a))
