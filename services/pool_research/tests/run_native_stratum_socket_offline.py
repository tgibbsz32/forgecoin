"""Optional C++ RandomX over local Stratum-shaped TCP, with fake daemon.

Requires a trusted externally compiled randomx_worker and MSYS runtime on PATH
where applicable. No production daemon, keys, funds, blocks or pool credits.
"""
import argparse
import asyncio
import json
from pathlib import Path

from services.pool_research.bound_job import _varint
from services.pool_research.daemon_job_source import DaemonJobSource
from services.pool_research.native_stratum_research import NativeResearchListener
from services.pool_research.persistent_randomx import PersistentRandomXAdapter
from services.pool_research.test_daemon_job_source import FakeDaemon, GENESIS


async def test(executable: Path):
    adapter=PersistentRandomXAdapter(executable,timeout=30)
    fake=FakeDaemon()
    def factory():
        return DaemonJobSource(fake,expected_genesis_hash=GENESIS,
              expected_nettype="testnet",wallet_address="DISPOSABLE_TEST_ADDRESS")
    listener=NativeResearchListener(factory,adapter,difficulty=1)
    reader=writer=None
    try:
        port=await listener.start()
        reader,writer=await asyncio.open_connection("127.0.0.1",port)
        async def send(req_id,method,params):
            writer.write((json.dumps({"id":req_id,"method":method,"params":params})+"\n").encode())
            await writer.drain()
            return json.loads(await asyncio.wait_for(reader.readline(),timeout=35))
        login=await send(1,"login",{"login":"fixture-only","algo":["rx/0"]})
        if login["error"] is not None:
            raise AssertionError(login["error"]["message"])
        session=login["result"]
        job=session["job"]
        blob=bytes.fromhex(job["blob"])
        offset=0
        for _ in range(3):
            offset=_varint(blob,offset)
        offset+=32
        nonce="01020304"
        patched=blob[:offset]+bytes.fromhex(nonce)+blob[offset+4:]
        digest=await asyncio.to_thread(adapter,bytes.fromhex(job["seed_hash"]),patched)
        claim={"id":session["id"],"job_id":job["job_id"],"nonce":nonce,"result":digest.hex()}
        answer=await send(2,"submit",claim)
        if answer["error"] is not None:
            raise AssertionError(answer["error"]["message"])
        if answer["result"]!={"status":"POW_THRESHOLD_MET_UNCREDITED","credited":False,
                              "submitted_block":False}:
            raise AssertionError("unsafe success status")
        denied=await send(3,"submit",claim)
        if denied["error"] is None:
            raise AssertionError("replayed nonce was accepted")
        print("PASS: native C++ RandomX digest through loopback Stratum socket")
        print("PASS: native duplicate rejection, no block or payout credited")
        print("NOTICE: fully synthetic daemon fixture; production Stratum NOT proven")
    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()
        await listener.close()
        adapter.close()


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--executable",type=Path,required=True)
    args=p.parse_args()
    asyncio.run(test(args.executable))
