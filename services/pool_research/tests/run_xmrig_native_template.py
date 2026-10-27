"""One-shot native-template XMRig test, strictly unprivileged in loopback-only netns.

Produces an uncredited *offline* full block candidate from a real miner nonce.
NEVER contacts a daemon, submits a block, credits rewards or pays wallets.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import resource
import secrets
import signal
import subprocess
import tempfile
import time

from services.pool_research.isolated_miner_candidate import IsolatedMinerJob
from services.pool_research.persistent_randomx import PersistentRandomXAdapter
from services.pool_research.stratum_protocol import MAX_FRAME_BYTES, ProtocolError, parse_request
from services.pool_research.template_adapter import validate_template
from services.pool_research.tests.run_xmrig_synthetic import check_isolation


def _read_template(path):
    if path.stat().st_size > 1048576:
        raise ValueError("oversized native capture")
    with path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    return data, validate_template(data)


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--xmrig", type=Path, required=True)
    parser.add_argument("--worker", type=Path, required=True)
    parser.add_argument("--xmrig-sha256", required=True)
    parser.add_argument("--worker-sha256", required=True)
    args = parser.parse_args()
    check_isolation()
    if args.capture.resolve() == args.output.resolve() or args.output.exists():
        raise ValueError("candidate output must be a new, private file")
    if not args.output.parent.is_dir():
        raise ValueError("private output directory missing")
    for path, expected in ((args.xmrig, args.xmrig_sha256),
                           (args.worker, args.worker_sha256)):
        if (len(expected) != 64 or
                hashlib.sha256(path.read_bytes()).hexdigest() != expected.lower()):
            raise RuntimeError("executable digest mismatch")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    version = subprocess.run([str(args.xmrig.resolve()), "--version"], timeout=5,
                             check=True, capture_output=True, text=True)
    if "6.26.0" not in version.stdout:
        raise RuntimeError("unexpected XMRig version")
    source, template = _read_template(args.capture)
    # Single-worker, fresh random reserved bytes; the full native block is
    # reconstructed ONLY after independently verifying the miner's nonce.
    reserve = secrets.token_hex(8)
    if reserve == template.blocktemplate_blob[
            template.reserved_offset:template.reserved_offset + 8].hex():
        raise RuntimeError("random reserved field unexpectedly unchanged")
    job = IsolatedMinerJob(template, reserve)
    adapter = PersistentRandomXAdapter(args.worker, timeout=10)
    done = asyncio.Event()
    errors = []
    server = None
    miner = None
    start = time.monotonic()

    async def send(writer, rid, result=None, error=None):
        writer.write((json.dumps({"id": rid, "jsonrpc": "2.0",
                                 "result": result, "error": error}) + "\n").encode())
        await asyncio.wait_for(writer.drain(), 3)

    async def handle(reader, writer):
        connection = secrets.token_hex(16)
        authenticated = False
        try:
            for _ in range(12):
                line = await asyncio.wait_for(reader.readline(), 30)
                if not line:
                    return
                if len(line) > MAX_FRAME_BYTES or not line.endswith(b"\n"):
                    raise ProtocolError("oversized or partial request")
                req = parse_request(line.strip())
                method, rid, params = req["method"], req["id"], req["params"]
                if method == "login" and not authenticated:
                    if "algo" in params and "rx/0" not in params["algo"]:
                        raise ProtocolError("client has no rx/0 support")
                    authenticated = True
                    await send(writer, rid, {"id": connection,
                        "status": "ISOLATED_TEST_ONLY", "job": {
                            "job_id": job.job_id,
                            "blob": job.prepared.blockhashing_blob.hex(),
                            "seed_hash": job.prepared.seed_hash.hex(),
                            "height": 1, "target": "ffffffff", "algo": "rx/0"}})
                elif method == "keepalived" and authenticated:
                    await send(writer, rid, {"status": "KEEPALIVED"})
                elif method == "submit" and authenticated:
                    if params["id"] != connection or params["job_id"] != job.job_id:
                        raise ProtocolError("wrong bound session or job")
                    candidate = await asyncio.to_thread(job.verify_submission,
                        params["job_id"], params["nonce"], params["result"], adapter)
                    record = dict(source["result"])
                    record.update({
                        "blocktemplate_blob": candidate.full_block_blob.hex(),
                        "blockhashing_blob": candidate.hashing_blob.hex(),
                        "nonce_hex": candidate.nonce_hex,
                        "reserve_hex": candidate.reserve_hex,
                        "native_digest_hex": candidate.digest_hex,
                        "nonce_offset": job.nonce_offset,
                        "verified_by_native_randomx": True,
                        "credited": False,
                        "source": "isolated-xmrig-native-template-test"})
                    # Exclusively create; never mutate the original capture.
                    with args.output.open("x", encoding="utf-8") as dest:
                        json.dump({"result": record}, dest, separators=(",", ":"))
                    await send(writer, rid, {"status": "POW_THRESHOLD_MET_UNCREDITED",
                                             "credited": False, "recorded": True})
                    done.set()
                    return
                else:
                    raise ProtocolError("login required or unsupported request")
        except (Exception,) as error:
            errors.append(type(error).__name__ + ": " + str(error)[:120])
            # No success response and no share credit on any failure.
        finally:
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), 3)
            except (OSError, asyncio.TimeoutError):
                pass

    try:
        server = await asyncio.start_server(handle, "127.0.0.1", 0,
                                            limit=MAX_FRAME_BYTES)
        port = server.sockets[0].getsockname()[1]
        with tempfile.TemporaryDirectory(prefix="frg-miner-bridge-",
                                         dir=args.output.parent) as temp:
            folder = Path(temp)
            config = {"autosave": False, "background": False, "colors": False,
                      "donate-level": 0, "donate-over-proxy": 0,
                      "http": {"enabled": False}, "opencl": False, "cuda": False,
                      "randomx": {"init": 1, "mode": "light", "numa": False,
                                  "1gb-pages": False, "rdmsr": False, "wrmsr": False},
                      "cpu": {"enabled": True, "rx": [-1], "huge-pages": False,
                              "asm": False, "yield": True, "memory-pool": False},
                      "retries": 1, "retry-pause": 1, "print-time": 0,
                      "pools": [{"algo": "rx/0", "url": f"127.0.0.1:{port}",
                                 "user": "isolated-template-only", "pass": "x",
                                 "tls": False, "keepalive": False}]}
            config_path = folder / "config.json"
            config_path.write_text(json.dumps(config))
            with (folder / "client.log").open("wb") as log:
                miner = subprocess.Popen(
                    [str(args.xmrig.resolve()), "--config", str(config_path)],
                    cwd=folder, stdin=subprocess.DEVNULL, stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=True)
                while time.monotonic() - start < 45 and not done.is_set():
                    if miner.poll() is not None:
                        break
                    await asyncio.sleep(0.1)
                if not done.is_set():
                    raise AssertionError("no independently verified miner nonce; "
                                         + "; ".join(errors[-3:]))
    finally:
        if miner is not None:
            try:
                os.killpg(miner.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                await asyncio.to_thread(miner.wait, timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(miner.pid, signal.SIGKILL)
                await asyncio.to_thread(miner.wait, timeout=3)
        if server is not None:
            server.close()
            await server.wait_closed()
        adapter.close()
    if not done.is_set() or not args.output.is_file():
        raise AssertionError("no durable verified candidate")
    print("PASS: real XMRig nonce + native RandomX verified against daemon-captured job")
    print("PASS: full nonce/coinbase-reserve candidate reconstructed; credited=0")
    print("OFFLINE_ONLY: no block submission, daemon RPC, or wallet activity")


if __name__ == "__main__":
    asyncio.run(main())
