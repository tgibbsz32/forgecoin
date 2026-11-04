#!/usr/bin/env python3
"""Two-node FRG prelaunch network handshake on loopback-only, disposable chains.

The nodes are forbidden from using DNS seeds, public peer connections, wallets,
block mining or production LMDB directories. This is NOT a reorganization test.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from smoke_frozen_prelaunch_daemon import call_rpc, require_result, take_free_port

ROOT = Path(__file__).resolve().parents[1]
GENESIS = "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"


def unique_ports(count: int) -> list[int]:
    out: list[int] = []
    while len(out) < count:
        port = take_free_port()
        if port not in out:
            out.append(port)
    return out


def launch(binary: Path, node: Path, stdout_file, p2p_port: int,
           rpc_port: int, *, peer: int | None) -> subprocess.Popen:
    # A nonempty --add-exclusive-node restricts outbound connections to the
    # sole explicit localhost address, and --out-peers 0 on node 0 disables
    # all outbound peer discovery/connection attempts.
    cmd = [
        str(binary.resolve()), "--non-interactive", "--no-igd", "--no-zmq",
        "--hide-my-port", "--allow-local-ip", "--disable-dns-checkpoints",
        "--check-updates", "disabled",
        "--p2p-bind-ip", "127.0.0.1", "--p2p-bind-port", str(p2p_port),
        "--rpc-bind-ip", "127.0.0.1", "--rpc-bind-port", str(rpc_port),
        "--data-dir", str(node), "--log-file", str(node / "daemon.log"),
        "--out-peers", "0" if peer is None else "1",
        "--in-peers", "2" if peer is None else "0",
    ]
    if peer is not None:
        cmd.extend(["--add-exclusive-node", f"127.0.0.1:{peer}"])
    return subprocess.Popen(
        cmd, stdin=subprocess.DEVNULL, stdout=stdout_file,
        stderr=subprocess.STDOUT,
        env={**os.environ, "HOME": str(node.parent)},
        close_fds=True,
    )


def safe_info(port: int) -> dict:
    res = call_rpc(port, "get_info", {}, plain=True)
    if res.get("status") != "OK":
        raise AssertionError(f"Node on RPC port {port} returned non-OK status")
    if res.get("nettype") != "mainnet" or res.get("height") != 1:
        raise AssertionError("Loopback peer is not at MAINNET genesis-only height")
    return res


def verified_genesis(port: int) -> None:
    result = require_result(
        call_rpc(port, "get_block_header_by_height", {"height": 0}),
        "get_block_header_by_height",
    )
    header = result.get("block_header")
    if not isinstance(header, dict):
        raise AssertionError("Missing genesis block header from peer")
    if header.get("height") != 0 or header.get("nonce") != 20261026:
        raise AssertionError("Peer genesis height/nonce mismatch")
    if header.get("hash") != GENESIS:
        raise AssertionError("Peer genesis hash differs from frozen 20261026 identity")


def run(binary: Path, manifest: dict, max_seconds: int) -> None:
    if os.name == "nt":
        raise SystemExit("Only use in an isolated Linux CI runner")
    if not binary.is_file():
        raise AssertionError("Compiled daemon binary missing")
    if (manifest.get("release_authorized") is not False
            or manifest.get("consensus_guard_stage") != "draft-unbuilt"
            or manifest.get("genesis_nonce") != 20261026
            or manifest.get("genesis_hash") != GENESIS
            or manifest.get("mined_blocks_permitted_before_launch") != 0
            or manifest.get("pool", {}).get("payouts_enabled") is not False
            or manifest.get("pool", {}).get("stratum_public") is not False):
        raise AssertionError("Prelaunch chain/payout release interlocks did not match")

    a_p2p, a_rpc, b_p2p, b_rpc = unique_ports(4)
    with tempfile.TemporaryDirectory(prefix="frg-local-peer-handshake-") as folder:
        tmp = Path(folder)
        procs: list[subprocess.Popen] = []
        logs = []
        try:
            for i, (p2p_port, rpc_port, peer) in enumerate((
                (a_p2p, a_rpc, None),
                (b_p2p, b_rpc, a_p2p),
            )):
                node = tmp / f"node-{i}"
                node.mkdir()
                log = (tmp / f"node-{i}-output.log").open("wb")
                logs.append(log)
                procs.append(launch(binary, node, log, p2p_port, rpc_port, peer=peer))
            deadline = time.monotonic() + max_seconds
            handshake = False
            while time.monotonic() < deadline:
                for i, proc in enumerate(procs):
                    if proc.poll() is not None:
                        raise AssertionError(f"Isolated peer {i} terminated before P2P handshake")
                try:
                    info_a, info_b = safe_info(a_rpc), safe_info(b_rpc)
                    in_count = info_a.get("incoming_connections_count", 0)
                    out_count = info_b.get("outgoing_connections_count", 0)
                    if in_count >= 1 and out_count >= 1:
                        if info_a.get("outgoing_connections_count") != 0:
                            raise AssertionError("P2P listener initiated unexpected outbound connection")
                        if info_b.get("incoming_connections_count") != 0:
                            raise AssertionError("P2P connector allowed unexpected inbound connection")
                        verified_genesis(a_rpc)
                        verified_genesis(b_rpc)
                        handshake = True
                        break
                except (OSError, TimeoutError, ValueError, ConnectionError):
                    pass
                time.sleep(0.5)
            if not handshake:
                raise AssertionError("Isolated prelaunch peers did not handshake")
            print("PASS: two mainnet identity nodes handshook via loopback-only P2P", flush=True)
            # A once-valid pre-guard mined block must not be accepted or
            # propagated as a new canonical block by these locked peers.
            fixture = json.loads((ROOT / "tests/mainnet/fixtures/isolated_20261026_block1.json").read_text(encoding="utf-8"))
            if (fixture.get("expected_genesis_hash") != GENESIS
                    or fixture.get("accepted_block_hash") != "9755a4f129f97b7865e5897e79abf5fea89dec2ba776d53fb9d01942b9f7ba9e"):
                raise AssertionError("Historical mined block fixture identity mismatch")
            rejected = call_rpc(a_rpc, "submitblock", [fixture["serialized_block_hex"]])
            if (not isinstance(rejected.get("error"), dict)
                    or rejected["error"].get("message") != "Block not accepted"):
                raise AssertionError("P2P-connected prelaunch node accepted mined block")
            time.sleep(2)
            for p in (a_rpc, b_rpc):
                safe_info(p)
                verified_genesis(p)
            print("PASS: both peer chains remain genesis-only, no block production", flush=True)
        except Exception:
            for i in range(len(logs)):
                path = tmp / f"node-{i}-output.log"
                if path.exists():
                    excerpt = path.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]
                    print(f"DIAGNOSTIC node-{i} last 30 lines:\n" + "\n".join(excerpt)[-5000:], flush=True)
            raise
        finally:
            for proc in procs:
                if proc.poll() is None:
                    proc.terminate()
            for proc in procs:
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
            for handle in logs:
                handle.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "config/mainnet.identity.json")
    parser.add_argument("--max-seconds", type=int, default=75)
    args = parser.parse_args()
    if not 10 <= args.max_seconds <= 110:
        raise SystemExit("max-seconds must be between 10 and 110")
    run(args.daemon, json.loads(args.manifest.read_text(encoding="utf-8")), args.max_seconds)


if __name__ == "__main__":
    main()
