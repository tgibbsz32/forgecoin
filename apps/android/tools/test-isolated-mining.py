#!/usr/bin/env python3
"""Exercise the Android foreground miner on a disposable, loopback FAKECHAIN."""
import argparse
import contextlib
import json
from pathlib import Path
import socketserver
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from smoke_regtest_reorg import FROZEN_GENESIS, call_rpc, header, info, launch, require_result, unique_ports, wait_ready

ADDRESS = "YnJ4sygA2VbA4nvoXssZcSKh4fwsw4g3DaujrVCDXSwWGuXwnYTfNsKPVunwuAf8joPEWfePpMh6CEsyEqMpQz2i2uFy112XA"
PACKAGE = "org.forgecoin.p2ptest.isolatedqa"
RUNNER = PACKAGE + ".test/androidx.test.runner.AndroidJUnitRunner"

def adb(serial, *args, timeout=15):
    try:
        return subprocess.run(["adb", "-s", serial, *args], capture_output=True,
                              text=True, check=True, timeout=timeout).stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        for output in (exc.stdout, exc.stderr):
            if output:
                print(output.decode(errors="replace") if isinstance(output, bytes) else output, flush=True)
        raise

@contextlib.contextmanager
def reverse(serial, port):
    remote = int(adb(serial, "reverse", "tcp:0", f"tcp:{port}"))
    try:
        yield f"127.0.0.1:{remote}"
    finally:
        try:
            adb(serial, "reverse", "--remove", f"tcp:{remote}")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            # The ephemeral server is still closed below even if ADB detached.
            print(f"ADB could not remove its disposable reverse mapping: {exc}", file=sys.stderr)

def instrument(serial, endpoint, argument, method, class_name="NativeMiningServiceInstrumentedTest", qa_node=None):
    extras = ("-e", "frgQaNodePort", qa_node.split(":")[1]) if qa_node else ()
    result = adb(serial, "shell", "am", "instrument", "-w", "-r",
                 "-e", argument, endpoint, *extras, "-e", "class",
                 "org.forgecoin.p2ptest." + class_name + "#" + method,
                 RUNNER, timeout=125)
    print(result, flush=True)
    if "OK (1 test)" not in result or "INSTRUMENTATION_STATUS_CODE: -3" in result:
        raise AssertionError("Android mining instrumentation did not pass")

@contextlib.contextmanager
def fixture_pool(rpc):
    # Uses the real disposable daemon template and native PoW verification.
    # No block submission, pool credit, payout, or public listener.
    template = require_result(call_rpc(rpc, "get_block_template",
        {"wallet_address": ADDRESS, "reserve_size": 8}), "get_block_template")
    blob = bytes.fromhex(template["blockhashing_blob"])
    offset = 0
    for _ in range(3):
        while blob[offset] & 128:
            offset += 1
        offset += 1
    offset += 32
    if offset + 4 > len(blob):
        raise ValueError("Invalid native hashing blob")
    counts = [0, 0]
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(40)
            while True:
                line = self.rfile.readline(8193)
                if not line or len(line) > 8192:
                    return
                # One ADB reverse mapping carries both Stratum and the miner's
                # two read-only identity probes. This fixture is not a public proxy.
                if line.startswith(b"POST "):
                    path = line.split()[1].decode("ascii")
                    length = None
                    while True:
                        field = self.rfile.readline(4097)
                        if field in (b"\r\n", b"\n", b""):
                            break
                        if field.lower().startswith(b"content-length:"):
                            length = int(field.split(b":", 1)[1])
                    if length is None or not 0 < length <= 4096:
                        return
                    body = json.loads(self.rfile.read(length))
                    if path == "/get_info":
                        reply = call_rpc(rpc, "get_info", {}, plain=True)
                    elif path == "/json_rpc" and body.get("method") == "get_block_header_by_height":
                        reply = call_rpc(rpc, "get_block_header_by_height", {"height": 0})
                    else:
                        return
                    payload = json.dumps(reply).encode()
                    self.wfile.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\nContent-Length: "
                                     + str(len(payload)).encode() + b"\r\n\r\n" + payload)
                    return
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                error = None
                result = {"status": "OK"}
                if method == "login":
                    if params.get("login") != ADDRESS:
                        raise AssertionError("Unexpected mining identity")
                    result.update(id="isolated-android", job={
                        "job_id": "one-private-job", "blob": blob.hex(),
                        "seed_hash": template["seed_hash"], "target": "ffffff0f",
                        "height": template["height"], "algo": "rx/0"})
                elif method == "submit":
                    nonce = bytes.fromhex(params.get("nonce", ""))
                    verified = False
                    if (counts[0] == 0 and len(nonce) == 4 and
                        params.get("id") == "isolated-android" and
                        params.get("job_id") == "one-private-job"):
                        hashing = blob[:offset] + nonce + blob[offset+4:]
                        response = call_rpc(rpc, "calc_pow", {
                            "major_version": blob[0], "height": template["height"],
                            "seed_hash": template["seed_hash"], "block_blob": hashing.hex()})
                        digest = response.get("result")
                        verified = (isinstance(digest, str) and len(digest) == 64 and
                                    digest == params.get("result") and
                                    int.from_bytes(bytes.fromhex(digest), "little") * 16 < 1 << 256)
                    if verified:
                        counts[0] += 1
                    else:
                        counts[1] += 1
                        error = {"code": -1, "message": "Private QA stale or invalid share"}
                        result = None
                elif method != "keepalived":
                    raise AssertionError("Unexpected private Stratum method")
                self.wfile.write((json.dumps({"jsonrpc":"2.0", "id":request["id"],
                    "result":result, "error":error}) + "\n").encode())
    class Server(socketserver.ThreadingTCPServer):
        daemon_threads = True
    with Server(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server.server_address[1], counts
        finally:
            server.shutdown()
            thread.join()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--daemon", type=Path, required=True)
    p.add_argument("--device", required=True)
    p.add_argument("--mode", choices=("solo", "pool", "both", "wallet", "send"), default="both")
    args = p.parse_args()
    with tempfile.TemporaryDirectory(prefix="frg-android-fakechain-") as work:
        path = Path(work)
        p2p, rpc = unique_ports(2)
        with (path / "stdout.log").open("wb") as log:
            process = launch(args.daemon, path, p2p, rpc, log, offline=True)
            try:
                start = wait_ready(process, rpc, time.monotonic() + 30)
                assert start["height"] == 1 and header(rpc, 0)["hash"] == FROZEN_GENESIS
                if args.mode in ("wallet", "send"):
                    method = ("synchronizesReceivedFrgFromDisposableChain" if args.mode == "wallet"
                              else "signsConfirmsAndReceivesIsolatedTransfer")
                    with reverse(args.device, rpc) as endpoint:
                        instrument(args.device, endpoint, "frgWalletEndpoint", method,
                                   "NativeFrgWalletInstrumentedTest")
                if args.mode in ("solo", "both"):
                    with reverse(args.device, rpc) as endpoint:
                        instrument(args.device, endpoint, "frgSoloEndpoint",
                                   "directSoloReceivesAcceptedBlockAcknowledgment")
                    assert info(rpc)["height"] > 1
                    print(f"PASS: disposable solo chain height {info(rpc)['height']}", flush=True)
                if args.mode in ("pool", "both"):
                    with fixture_pool(rpc) as (port, counts):
                        with reverse(args.device, port) as endpoint:
                            instrument(args.device, endpoint, "frgPoolEndpoint",
                                       "privateStratumReportsAcceptedAndRejectedShares", qa_node=endpoint)
                    assert counts[0] == 1 and counts[1] > 0
                    print(f"PASS: native PoW verified; accepted={counts[0]}, rejected={counts[1]}; no pool credit", flush=True)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)

if __name__ == "__main__":
    main()
