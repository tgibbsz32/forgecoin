#!/usr/bin/env python3
"""Actual native pool Stratum submission on a disposable one-block FAKECHAIN.

Uses localhost only, a public test payout destination, fixed regtest difficulty
one, genuine native RandomX, and the *real* C pool and frozen candidate daemon.
The consensus MAINNET prelaunch mining lock remains compiled-in, untouched.
No wallet RPC, view-key acquisition, keys, payment, public listener or Oracle.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import tempfile
import time
import urllib.error

from smoke_native_pool_regtest import (
    RPC_PORT, local_stats, require_manifest, test_config, wait_stats,
)
from smoke_regtest_reorg import (
    FROZEN_GENESIS, header, info, launch, take_free_port, wait_ready,
)

ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r"^[0-9a-fA-F]+$")


def stratum_send(sock: socket.socket, request: dict) -> None:
    payload = json.dumps(request, separators=(",", ":")).encode("ascii") + b"\n"
    if len(payload) > 4096:
        raise AssertionError("Overlong Stratum test request")
    sock.sendall(payload)


def stratum_reply(reader, request_id: int) -> dict:
    for _ in range(12):
        line = reader.readline(65537)
        if not line or len(line) > 65536:
            raise AssertionError("Missing or oversized native Stratum response")
        response = json.loads(line)
        if not isinstance(response, dict):
            raise AssertionError("Non-object native Stratum response")
        if response.get("id") == request_id:
            return response
        # A legitimate pool may send asynchronous new-job notifications.
        if response.get("method") == "job":
            continue
        raise AssertionError("Unexpected Stratum response/request ID")
    raise AssertionError("Never received requested native Stratum response")


def check_login(response: dict) -> tuple[str, dict]:
    if response.get("error") is not None:
        raise AssertionError(f"Stratum login error {response['error']!r}")
    result = response.get("result")
    if not isinstance(result, dict) or result.get("status") != "OK":
        raise AssertionError("Native Stratum did not authenticate test public address")
    client_id, job = result.get("id"), result.get("job")
    if (not isinstance(client_id, str) or len(client_id) != 32
            or not HEX.fullmatch(client_id)):
        raise AssertionError("Invalid native Stratum miner ID")
    if not isinstance(job, dict):
        raise AssertionError("No native Stratum job issued")
    if job.get("height") != 1:
        raise AssertionError("Unexpected pre-mined FAKECHAIN job height")
    for key, length in (("seed_hash", 64), ("job_id", 32), ("target", 8)):
        value = job.get(key)
        if not isinstance(value, str) or len(value) != length or not HEX.fullmatch(value):
            raise AssertionError(f"Malformed native Stratum job {key}")
    blob = job.get("blob")
    if (not isinstance(blob, str) or len(blob) < 120
            or len(blob) > 8192 or len(blob) % 2 or not HEX.fullmatch(blob)):
        raise AssertionError("Malformed native RandomX Stratum hashing blob")
    return client_id, job


def native_pow(pow_binary: Path, job: dict) -> tuple[str, str]:
    if not pow_binary.is_file():
        raise AssertionError("Missing exact-native RandomX fixture executable")
    result = subprocess.run(
        [str(pow_binary.resolve()), job["seed_hash"], job["blob"]],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        timeout=50, check=True, env={k: v for k, v in os.environ.items()
                                     if k != "MONERO_RANDOMX_FULL_MEM"},
    )
    fields = result.stdout.strip().split()
    if (len(fields) != 2 or len(fields[0]) != 8 or len(fields[1]) != 64
            or not all(HEX.fullmatch(f) for f in fields)):
        raise AssertionError("Invalid native RandomX test hash result")
    return fields[0], fields[1]


def wait_accepted(node_port: int, web_port: int,
                  pool_process: subprocess.Popen, deadline: float) -> tuple[dict, dict]:
    last = None
    while time.monotonic() < deadline:
        if pool_process.poll() is not None:
            raise AssertionError("Native C pool exited after Stratum block submission")
        try:
            node = info(node_port)
            stats = local_stats(web_port)
            last = (node, stats)
            if (node.get("height") == 2
                    and stats.get("pool_blocks_found") == 1):
                return node, stats
        except (TimeoutError, OSError, ConnectionError, ValueError, urllib.error.URLError):
            pass
        time.sleep(0.4)
    raise AssertionError(f"Pool Stratum candidate was not durably acknowledged: {last!r}")


def run(daemon: Path, pool_binary: Path, pow_binary: Path,
        manifest: dict, max_seconds: int) -> None:
    if os.name == "nt":
        raise SystemExit("Run only in disposable Linux CI")
    address = require_manifest(manifest)
    if any(not b.is_file() for b in (daemon, pool_binary, pow_binary)):
        raise AssertionError("Missing reviewed full-stack native test binaries")

    ports = []
    while len(ports) < 4:
        candidate = take_free_port()
        if candidate != RPC_PORT and candidate not in ports:
            ports.append(candidate)
    p2p_port, pool_port, web_port, wallet_rpc_absent = ports
    with tempfile.TemporaryDirectory(prefix="frg-stratum-pow-fakechain-") as folder:
        home = Path(folder)
        node_dir, pool_dir = home / "node", home / "pool-data"
        node_dir.mkdir()
        pool_dir.mkdir()
        config = test_config(address, pool_dir, pool_port, web_port, wallet_rpc_absent)
        logs = [(home / n).open("wb") for n in ("daemon.log", "pool.log")]
        processes = []
        try:
            node = launch(daemon, node_dir, p2p_port, RPC_PORT, logs[0], offline=True)
            processes.append(node)
            deadline = time.monotonic() + max_seconds
            if (wait_ready(node, RPC_PORT, deadline).get("height") != 1
                    or header(RPC_PORT, 0)["hash"] != FROZEN_GENESIS):
                raise AssertionError("Only genesis-only FAKECHAIN mining is approved")

            env = {k: v for k, v in os.environ.items()
                   if k != "MONERO_RANDOMX_FULL_MEM"}
            pool_proc = subprocess.Popen(
                [str(pool_binary.resolve()), "--config-file", str(config)],
                cwd=str(home), stdin=subprocess.DEVNULL,
                stdout=logs[1], stderr=subprocess.STDOUT,
                close_fds=True, env=env,
            )
            processes.append(pool_proc)
            stats = wait_stats(pool_proc, web_port, deadline, 0, require_template=True)
            if (stats.get("network_height") != 0
                    or stats.get("pool_blocks_found") != 0
                    or stats.get("pool_fee") != 0.01
                    or stats.get("allow_self_select") != 0):
                raise AssertionError("Unsafe native pool pre-mining state")

            with socket.create_connection(("127.0.0.1", pool_port), timeout=8) as sock:
                sock.settimeout(20)
                with sock.makefile("rb") as reader:
                    stratum_send(sock, {
                        "id": 1, "jsonrpc": "2.0", "method": "login",
                        "params": {"login": address, "pass": "x",
                                   "agent": "FRG-Isolated-Regtest-RandomX/1"},
                    })
                    client_id, job = check_login(stratum_reply(reader, 1))
                    stratum_send(sock, {"id": 2, "jsonrpc": "2.0",
                                        "method": "keepalived",
                                        "params": {"id": client_id}})
                    keepalive = stratum_reply(reader, 2)
                    if (keepalive.get("error") is not None
                            or keepalive.get("result", {}).get("status") != "KEEPALIVED"):
                        raise AssertionError("Native Stratum keepalived failed")
                    # Malformed nonce must be rejected BEFORE any RandomX hash
                    # calculation or share credit.
                    stratum_send(sock, {
                        "id": 3, "jsonrpc": "2.0", "method": "submit",
                        "params": {"id": client_id, "job_id": job["job_id"],
                                   "nonce": "wrong", "result": "0" * 64},
                    })
                    malformed = stratum_reply(reader, 3)
                    if malformed.get("error") is None:
                        raise AssertionError("Pool accepted an invalid Stratum nonce")

                    nonce, result_hash = native_pow(pow_binary, job)
                    stratum_send(sock, {
                        "id": 4, "jsonrpc": "2.0", "method": "submit",
                        "params": {"id": client_id, "job_id": job["job_id"],
                                   "nonce": nonce, "result": result_hash},
                    })
                    accepted = stratum_reply(reader, 4)
                    if (accepted.get("error") is not None
                            or accepted.get("result", {}).get("status") != "OK"):
                        raise AssertionError(f"Native RandomX Stratum share rejected: {accepted!r}")

                    # Same exact hash/nonce/job must never create another
                    # candidate, even if first daemon RPC is still pending.
                    stratum_send(sock, {
                        "id": 5, "jsonrpc": "2.0", "method": "submit",
                        "params": {"id": client_id, "job_id": job["job_id"],
                                   "nonce": nonce, "result": result_hash},
                    })
                    duplicate = stratum_reply(reader, 5)
                    if duplicate.get("error") is None:
                        raise AssertionError("Duplicate Stratum share was accepted")
                    _, stats = wait_accepted(RPC_PORT, web_port, pool_proc,
                                             time.monotonic() + max_seconds)
                    canonical = header(RPC_PORT, 1)
                    if (canonical.get("height") != 1
                            or canonical.get("prev_hash") != FROZEN_GENESIS
                            or canonical.get("difficulty") != 1):
                        raise AssertionError("Pool-submitted native block not canonical")
                    if (stats.get("pool_blocks_found") != 1
                            or stats.get("pool_fee") != 0.01
                            or stats.get("miner_balance") != 0.0):
                        raise AssertionError("Incorrect post-block pool statistics")
                    print(
                        "PASS: real native RandomX Stratum share and daemon-accepted "
                        "FAKECHAIN block, duplicate rejected, durable pool candidate "
                        "record counted once, 1% policy, no wallet/payout",
                        flush=True,
                    )
        except Exception:
            for path in (home / "daemon.log", home / "pool.log"):
                if path.exists():
                    recent = path.read_text(errors="replace").splitlines()[-50:]
                    print(f"DIAGNOSTIC {path.name}:\n" + "\n".join(recent)[-6000:],
                          flush=True)
            raise
        finally:
            for proc in reversed(processes):
                if proc.poll() is None:
                    proc.terminate()
            for proc in reversed(processes):
                with contextlib.suppress(subprocess.TimeoutExpired):
                    proc.wait(timeout=10)
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=5)
            for handle in logs:
                handle.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", type=Path, required=True)
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--pow-helper", type=Path, required=True)
    parser.add_argument("--max-seconds", type=int, default=100)
    args = parser.parse_args()
    if not 30 <= args.max_seconds <= 240:
        raise SystemExit("Bounded disposable test timeout out of range")
    manifest = json.loads((ROOT / "config/mainnet.identity.json").read_text())
    run(args.daemon, args.pool, args.pow_helper, manifest, args.max_seconds)


if __name__ == "__main__":
    main()
