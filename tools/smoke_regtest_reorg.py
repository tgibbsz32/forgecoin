#!/usr/bin/env python3
"""Disposable two-node FAKECHAIN reorganization acceptance (NOT mainnet).

Never touches real FRG mainnet, public peers, existing chain data, wallets or
payouts. Starts two isolated --regtest daemons with fixed difficulty 1 in temp
directories, mines distinct local forks, then connects only over 127.0.0.1.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

from smoke_frozen_prelaunch_daemon import call_rpc, require_result, take_free_port

ROOT = Path(__file__).resolve().parents[1]
FROZEN_GENESIS = "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"


def unique_ports(count: int) -> list[int]:
    ports: list[int] = []
    while len(ports) < count:
        port = take_free_port()
        if port not in ports:
            ports.append(port)
    return ports


def launch(binary: Path, directory: Path, p2p: int, rpc: int,
           log_handle, *, peer: int | None = None) -> subprocess.Popen:
    # No networking outside the namespace of this local CI runner:
    # physical P2P listener and RPC both bind 127.0.0.1. No DNS/IGD.
    cmd = [
        str(binary.resolve()), "--regtest", "--keep-fakechain",
        "--fixed-difficulty", "1",
        "--no-igd", "--no-zmq", "--hide-my-port", "--allow-local-ip",
        "--disable-dns-checkpoints", "--check-updates", "disabled",
        "--non-interactive",
        "--p2p-bind-ip", "127.0.0.1", "--p2p-bind-port", str(p2p),
        "--rpc-bind-ip", "127.0.0.1", "--rpc-bind-port", str(rpc),
        "--data-dir", str(directory),
        "--log-file", str(directory / "daemon.log"),
        "--log-level", "0",
        "--in-peers", "2" if peer is None else "0",
        "--out-peers", "0" if peer is None else "1",
    ]
    if peer is not None:
        cmd += ["--add-exclusive-node", f"127.0.0.1:{peer}"]
    return subprocess.Popen(
        cmd, stdin=subprocess.DEVNULL, stdout=log_handle,
        stderr=subprocess.STDOUT, close_fds=True,
        env={**os.environ, "HOME": str(directory.parent)},
    )


def info(port: int) -> dict:
    response = call_rpc(port, "get_info", {}, plain=True)
    if response.get("status") != "OK":
        raise AssertionError("Isolated regtest node has non-OK status")
    if response.get("nettype") not in ("fakechain", "regtest"):
        raise AssertionError("Regtest validation attempted against non-FAKECHAIN identity")
    return response


def header(port: int, height: int) -> dict:
    result = require_result(
        call_rpc(port, "get_block_header_by_height", {"height": height}),
        "get_block_header_by_height",
    )
    item = result.get("block_header")
    if not isinstance(item, dict) or item.get("height") != height:
        raise AssertionError("Missing expected regtest block header")
    return item


def wait_ready(proc: subprocess.Popen, port: int, deadline: float) -> dict:
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise AssertionError("Disposable regtest daemon exited early")
        try:
            return info(port)
        except (OSError, TimeoutError, ValueError, ConnectionError):
            time.sleep(0.5)
    raise AssertionError("Regtest daemon did not expose local RPC")


def mine(port: int, address: str, amount: int, nonce: int) -> list[str]:
    # Generating a native RandomX block may exceed the ordinary 2-second
    # smoke RPC timeout due to dataset initialization, even at difficulty 1.
    payload = {
        "jsonrpc": "2.0", "id": "isolated-regtest-only",
        "method": "generateblocks",
        "params": {
            "amount_of_blocks": amount,
            "wallet_address": address,
            "prev_block": "",
            "starting_nonce": nonce,
        },
    }
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/json_rpc",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=100) as reply:
            raw = reply.read(1_000_001)
    except urllib.error.HTTPError as exc:
        raw = exc.read(1_000_001)
    if len(raw) > 1_000_000:
        raise AssertionError("Regtest RPC response exceeds bounded local limit")
    response = require_result(json.loads(raw), "generateblocks")
    blocks = response.get("blocks")
    if not isinstance(blocks, list) or len(blocks) != amount:
        raise AssertionError("Regtest generateblocks did not mine the required blocks")
    if any(not isinstance(x, str) or len(x) != 64 for x in blocks):
        raise AssertionError("Malformed regtest block-hash response")
    return blocks


def run(binary: Path, manifest: dict, max_seconds: int) -> None:
    if os.name == "nt":
        raise SystemExit("Run only in disposable Linux CI, not on desktop/Oracle")
    if not binary.is_file():
        raise AssertionError("Compiled native daemon missing")
    if (manifest.get("release_authorized") is not False
            or manifest.get("consensus_guard_stage") != "draft-unbuilt"
            or manifest.get("mined_blocks_permitted_before_launch") != 0
            or manifest.get("genesis_hash") != FROZEN_GENESIS
            or manifest.get("pool", {}).get("payouts_enabled") is not False
            or manifest.get("pool", {}).get("stratum_public") is not False):
        raise AssertionError("Prelaunch mainnet lock is no longer frozen; abort test")

    address = manifest.get("pool", {}).get("operator_fee_address")
    if not isinstance(address, str) or not 90 <= len(address) <= 130:
        raise AssertionError("No public address suitable as regtest block destination")

    a_p2p, a_rpc, b_p2p, b_rpc = unique_ports(4)
    with tempfile.TemporaryDirectory(prefix="frg-fakechain-fork-") as temp:
        home = Path(temp)
        a = home / "fork-a"
        b = home / "fork-b"
        a.mkdir()
        b.mkdir()
        procs: list[subprocess.Popen] = []
        logs = []
        try:
            for node, pp, rp in ((a, a_p2p, a_rpc), (b, b_p2p, b_rpc)):
                log = (home / (node.name + ".log")).open("wb")
                logs.append(log)
                procs.append(launch(binary, node, pp, rp, log))

            deadline = time.monotonic() + max_seconds
            for proc, port in zip(procs, (a_rpc, b_rpc)):
                before = wait_ready(proc, port, deadline)
                if before.get("height") != 1:
                    raise AssertionError("Regtest did not start at isolated genesis")

            a0 = header(a_rpc, 0)["hash"]
            b0 = header(b_rpc, 0)["hash"]
            if a0 != b0 or a0 != FROZEN_GENESIS:
                raise AssertionError("Regtest genesis unexpected: should share frozen genesis")

            # Positive proof of competing forks, not just a restart/same chain:
            mine(a_rpc, address, 3, 13)
            mine(b_rpc, address, 5, 456)
            a_old_tip = header(a_rpc, 3)["hash"]
            b_tip = header(b_rpc, 5)["hash"]
            a_old_first = header(a_rpc, 1)["hash"]
            b_first = header(b_rpc, 1)["hash"]
            if a_old_first == b_first:
                raise AssertionError("Regtest forks are identical; no reorg demonstrated")
            if info(a_rpc)["height"] != 4 or info(b_rpc)["height"] != 6:
                raise AssertionError("Initial divergent chain heights unexpected")
            print("PASS: independent FAKECHAIN forks with distinct height-1 blocks", flush=True)
            # Native RandomX initialization is separate from P2P convergence;
            # do not count time spent mining toward the reorganization timeout.
            deadline = time.monotonic() + max_seconds

            # Reopen only node A with one explicit local B peer. --keep-fakechain
            # is essential: restarting must preserve the 3 mined A blocks.
            procs[0].terminate()
            procs[0].wait(timeout=10)
            log = (home / "fork-a-connected.log").open("wb")
            logs.append(log)
            procs[0] = launch(binary, a, a_p2p, a_rpc, log, peer=b_p2p)
            wait_ready(procs[0], a_rpc, deadline)

            matched = False
            while time.monotonic() < deadline:
                if any(p.poll() is not None for p in procs):
                    raise AssertionError("Regtest peer stopped during reorg")
                x = info(a_rpc)
                y = info(b_rpc)
                if x.get("height") == 6 and y.get("height") == 6:
                    if header(a_rpc, 5)["hash"] == b_tip:
                        matched = True
                        break
                time.sleep(0.6)
            if not matched:
                raise AssertionError("A did not reorganize to longer B fork")
            if header(a_rpc, 1)["hash"] != b_first:
                raise AssertionError("Orphaned first fork is still canonical")
            if header(a_rpc, 3)["hash"] == a_old_tip:
                raise AssertionError("Original shorter fork tip remained canonical")
            if header(a_rpc, 0)["hash"] != a0:
                raise AssertionError("Genesis changed during reorganization")
            print("PASS: shorter native FAKECHAIN fork reorganized to longer peer fork", flush=True)

            # The *same compiled daemon* must still refuse public mainnet
            # mining; the independent mainnet CI smoke tests prove that path.
            print("PASS: regtest-specific block production; no mainnet mining or payouts", flush=True)
        except Exception:
            for path in (home / "fork-a.log", home / "fork-a-connected.log", home / "fork-b.log"):
                if path.exists():
                    recent = path.read_text(encoding="utf-8", errors="replace").splitlines()[-25:]
                    print(f"DIAGNOSTIC {path.name}: " + "\n".join(recent)[-3500:], flush=True)
            raise
        finally:
            for proc in procs:
                if proc.poll() is None:
                    proc.terminate()
            for proc in procs:
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
    parser.add_argument("--manifest", type=Path, default=ROOT / "config/mainnet.identity.json")
    parser.add_argument("--max-seconds", type=int, default=140)
    args = parser.parse_args()
    if not (30 <= args.max_seconds <= 240):
        raise SystemExit("max-seconds outside bounded disposable CI window")
    run(args.daemon, json.loads(args.manifest.read_text(encoding="utf-8")), args.max_seconds)


if __name__ == "__main__":
    main()
