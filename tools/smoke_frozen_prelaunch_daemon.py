#!/usr/bin/env python3
"""Run the *built*, locked FRG mainnet daemon only on an isolated empty chain.

No public peers, public bind, wallet, mining, payout or production database.
This is a read-only genesis inspection and denial smoke test, NOT a PoW,
spend-authorization, double-spend, or network-acceptance test.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]


def take_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def call_rpc(port: int, method: str, params=None, *, plain: bool = False) -> dict:
    path = "/" + method if plain else "/json_rpc"
    body = params or {} if plain else {
        "jsonrpc": "2.0", "id": "forgecoin-prelaunch-smoke",
        "method": method, "params": params if params is not None else {},
    }
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            raw = response.read(1_000_001)
    except urllib.error.HTTPError as exc:
        raw = exc.read(1_000_001)
    if len(raw) > 1_000_000:
        raise AssertionError("Daemon RPC response exceeds fixed local smoke limit")
    answer = json.loads(raw)
    if not isinstance(answer, dict):
        raise AssertionError(f"Non-object RPC response: {method}")
    return answer


def require_result(answer: dict, method: str) -> dict:
    if answer.get("error") not in (None, {}):
        raise AssertionError(f"{method}: daemon reported RPC error")
    result = answer.get("result")
    if not isinstance(result, dict):
        raise AssertionError(f"{method}: missing JSON-RPC result")
    return result


def run(binary: Path, manifest: dict, max_seconds: int) -> None:
    if os.name == "nt":
        raise SystemExit("This smoke test requires an isolated Linux CI runner")
    if not binary.is_file():
        raise SystemExit("Native daemon executable does not exist")
    if manifest.get("release_authorized") is not False:
        raise AssertionError("Refusing unlocked/release-authorized manifest")
    if manifest.get("consensus_guard_stage") != "draft-unbuilt":
        raise AssertionError("Unexpected prelaunch consensus guard configuration")
    if manifest.get("mined_blocks_permitted_before_launch") != 0:
        raise AssertionError("Expected zero permitted mined blocks")
    if manifest.get("pool", {}).get("payouts_enabled") is not False:
        raise AssertionError("Refusing manifest with enabled payouts")
    if manifest.get("pool", {}).get("stratum_public") is not False:
        raise AssertionError("Refusing manifest with public Stratum")
    if manifest.get("genesis_nonce") != 20261026:
        raise AssertionError("Frozen identity mismatch")
    genesis = "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"
    if manifest.get("genesis_hash") != genesis:
        raise AssertionError("Frozen genesis hash mismatch")

    fee_address = manifest.get("pool", {}).get("operator_fee_address")
    if not isinstance(fee_address, str) or not 90 <= len(fee_address) <= 130:
        raise AssertionError("Missing public receiving-address fixture")
    rpc_port, p2p_port = take_free_port(), take_free_port()
    while p2p_port == rpc_port:
        p2p_port = take_free_port()

    with tempfile.TemporaryDirectory(prefix="frg-prelaunch-only-") as tmp:
        data = Path(tmp) / "isolated-chain"
        data.mkdir()
        cmd = [
            str(binary.resolve()),
            # Omit --testnet/--stagenet/--regtest: the daemon defaults to MAINNET.
            "--offline", "--non-interactive", "--no-zmq", "--no-igd",
            "--p2p-bind-ip", "127.0.0.1",
            "--p2p-bind-port", str(p2p_port),
            "--rpc-bind-ip", "127.0.0.1",
            "--rpc-bind-port", str(rpc_port),
            "--data-dir", str(data),
            "--log-file", str(data / "daemon.log"),
            "--log-level", "0",
        ]
        logpath = Path(tmp) / "startup-output.log"
        with logpath.open("wb") as handle:
            proc = subprocess.Popen(
                cmd, cwd=tmp,
                stdin=subprocess.DEVNULL, stdout=handle,
                stderr=subprocess.STDOUT,
                env={**os.environ, "HOME": tmp},
                close_fds=True,
            )
            try:
                deadline = time.monotonic() + max_seconds
                info = None
                while time.monotonic() < deadline:
                    if proc.poll() is not None:
                        raise AssertionError("Isolated daemon exited before genesis RPC became ready")
                    try:
                        candidate = call_rpc(rpc_port, "get_info", {}, plain=True)
                        if candidate.get("status") == "OK":
                            info = candidate
                            break
                    except (OSError, TimeoutError, ValueError):
                        pass
                    time.sleep(0.5)
                if info is None:
                    raise AssertionError("Isolated daemon RPC never became ready")
                if info.get("nettype") != "mainnet":
                    raise AssertionError("Daemon is not on mainnet identity")
                if info.get("height") != 1:
                    raise AssertionError(f"Fresh mainnet chain must be at height 1, got {info.get('height')}")
                header = require_result(call_rpc(
                    rpc_port, "get_block_header_by_height", {"height": 0}
                ), "get_block_header_by_height").get("block_header", {})
                if header.get("height") != 0:
                    raise AssertionError("Genesis block header height mismatch")
                if header.get("hash") != genesis:
                    raise AssertionError("Compiled genesis hash differs from frozen identity")
                if header.get("nonce") != 20261026:
                    raise AssertionError("Compiled genesis nonce differs from frozen identity")
                print("PASS: isolated frozen 20261026 genesis at local chain height 1", flush=True)

                # A valid public standard mainnet address; no private keys.
                template = call_rpc(rpc_port, "getblocktemplate", {
                    "wallet_address": fee_address, "reserve_size": 8
                })
                result = template.get("result")
                if isinstance(result, dict) and (
                    result.get("blocktemplate_blob") or result.get("blockhashing_blob")
                ):
                    raise AssertionError("Mainnet mining template was unexpectedly available")
                print("PASS: public mainnet mining template not exposed", flush=True)

                started = call_rpc(rpc_port, "start_mining", {
                    "miner_address": fee_address, "threads_count": 1,
                    "do_background_mining": False, "ignore_battery": True,
                }, plain=True)
                if started.get("status") == "OK":
                    raise AssertionError("Mainnet mining unexpectedly started")
                print("PASS: start_mining did not authorize mining", flush=True)

                after = call_rpc(rpc_port, "get_info", {}, plain=True)
                if after.get("height") != 1 or after.get("status") != "OK":
                    raise AssertionError("Prelaunch daemon left genesis-only height")
                print("PASS: mainnet remains at height 1; no mined block created", flush=True)
            except Exception:
                # Only our temporary, newly created offline daemon log is read.
                # Never print wallet material or arbitrary existing host files.
                for file in (logpath, data / "daemon.log"):
                    with contextlib.suppress(OSError):
                        lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
                        print(f"DIAGNOSTIC {file.name}: " + "\\n".join(lines[-35:])[-5000:], flush=True)
                raise
            finally:
                if proc.poll() is None:
                    proc.terminate()
                try:
                    proc.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=8)


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--daemon", type=Path, required=True)
    cli.add_argument("--manifest", type=Path, default=ROOT / "config/mainnet.identity.json")
    cli.add_argument("--max-seconds", type=int, default=60)
    args = cli.parse_args()
    if not 5 <= args.max_seconds <= 120:
        raise SystemExit("--max-seconds must be from 5 to 120")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    run(args.daemon, manifest, args.max_seconds)


if __name__ == "__main__":
    main()
