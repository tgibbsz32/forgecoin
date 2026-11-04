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
from forgecoin_chain_risk import assess as assess_chain_risk, take_snapshot as risk_snapshot

ROOT = Path(__file__).resolve().parents[1]
FROZEN_GENESIS = "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"

# Both branches become mature enough for 60-block native reward testing.
# Branch A's 66 formerly canonical blocks must ALL be reorganized when
# fork B's 70-block (higher cumulative work at fixed regtest diff 1) wins.
FORK_A_BLOCKS = 66
FORK_B_BLOCKS = 70
MINE_BATCH = 10


def unique_ports(count: int) -> list[int]:
    ports: list[int] = []
    while len(ports) < count:
        port = take_free_port()
        if port not in ports:
            ports.append(port)
    return ports


def launch(binary: Path, directory: Path, p2p: int, rpc: int,
           log_handle, *, peer: int | None = None, offline: bool = False) -> subprocess.Popen:
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
    if offline:
        cmd.append("--offline")
    if peer is not None:
        if offline:
            raise AssertionError("Cannot request a peer while in isolated offline mining mode")
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
    if response.get("status") != "OK":
        raise AssertionError(f"Regtest generateblocks returned status {response.get('status')!r}")
    if not isinstance(blocks, list) or len(blocks) != amount:
        raise AssertionError(
            f"Regtest generated {len(blocks) if isinstance(blocks, list) else 'no'} "
            f"blocks, expected {amount}"
        )
    if any(not isinstance(x, str) or len(x) != 64 for x in blocks):
        raise AssertionError("Malformed regtest block-hash response")
    return blocks


def mine_in_batches(port: int, address: str, total: int, starting_nonce: int) -> None:
    """Bound individual RPC calls; verify each native LMDB height advance."""
    if total < 1 or MINE_BATCH < 1:
        raise AssertionError("No regtest blocks requested")
    for mined in range(0, total, MINE_BATCH):
        amount = min(MINE_BATCH, total - mined)
        accepted = mine(port, address, amount, starting_nonce + mined * 2048)
        if len(accepted) != amount:
            raise AssertionError("Native generated-block count mismatch")
        expected = mined + amount + 1  # get_info.height includes genesis
        if info(port).get("height") != expected:
            raise AssertionError(
                f"Native regtest height mismatch after {mined + amount} blocks"
            )


def wait_for_reorg(a_rpc: int, b_rpc: int, winning_height: int,
                   winning_hash: str, processes: list[subprocess.Popen],
                   deadline: float) -> int:
    """Retry transient RPC stalls while a deep P2P reorg reorganizes LMDB.

    A short HTTP timeout is not evidence of consensus failure or success.
    Never bypass the final canonical hash/height checks; the deadline is hard.
    """
    last_heights = None
    transient_errors = 0
    while time.monotonic() < deadline:
        if any(p.poll() is not None for p in processes):
            raise AssertionError("Regtest peer stopped during deep reorg")
        try:
            x = info(a_rpc)
            y = info(b_rpc)
            last_heights = (x.get("height"), y.get("height"))
            if last_heights == (winning_height + 1, winning_height + 1):
                if header(a_rpc, winning_height)["hash"] == winning_hash:
                    return transient_errors
        except (OSError, TimeoutError, ConnectionError, ValueError):
            transient_errors += 1
        time.sleep(0.6)
    raise AssertionError(
        f"Native deep regtest reorg did not converge: expected={winning_height + 1}, "
        f"last_heights={last_heights!r}, transient_rpc_failures={transient_errors}"
    )


def observe_real_nodes(a_rpc: int, b_rpc: int, deadline: float) -> dict:
    """Use the exact read-only production observer against disposable native nodes.

    RPC may briefly stall during LMDB reorganization. Retry only until the
    finite test deadline, never silently accept incomplete/malformed samples.
    """
    snapshots = {}
    for name, port in (("fork-a", a_rpc), ("fork-b", b_rpc)):
        last_error = None
        while time.monotonic() < deadline:
            try:
                snapshots[name] = risk_snapshot(
                    f"http://127.0.0.1:{port}/json_rpc", window=96
                )
                break
            except (OSError, TimeoutError, ConnectionError, ValueError, KeyError) as exc:
                last_error = exc
                time.sleep(0.5)
        if name not in snapshots:
            raise AssertionError(
                f"Independent read-only observer could not verify {name}: "
                f"{type(last_error).__name__}"
            )
    return snapshots


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
                # CHECK_CORE_READY blocks generateblocks until synchronized.
                # Offline FAKECHAIN mode permits isolated local mining.
                procs.append(launch(binary, node, pp, rp, log, offline=True))

            deadline = time.monotonic() + max_seconds
            for proc, port in zip(procs, (a_rpc, b_rpc)):
                before = wait_ready(proc, port, deadline)
                if before.get("height") != 1:
                    raise AssertionError("Regtest did not start at isolated genesis")

            a0 = header(a_rpc, 0)["hash"]
            b0 = header(b_rpc, 0)["hash"]
            if a0 != b0 or a0 != FROZEN_GENESIS:
                raise AssertionError("Regtest genesis unexpected: should share frozen genesis")

            # Mine two separate native RandomX-validated FAKECHAIN forks.
            # At 60 confirmations A's first credited coinbase is mature.
            # A must lose 66 historical blocks to longer/higher-work B.
            if FORK_A_BLOCKS < 61 or FORK_B_BLOCKS <= FORK_A_BLOCKS:
                raise AssertionError("Deep-fork test depth below required maturity")
            mine_in_batches(a_rpc, address, FORK_A_BLOCKS, 13)
            mine_in_batches(b_rpc, address, FORK_B_BLOCKS, 456)
            a_old_tip = header(a_rpc, FORK_A_BLOCKS)["hash"]
            a_old_first = header(a_rpc, 1)["hash"]
            a_old_deep = header(a_rpc, FORK_A_BLOCKS - 1)["hash"]
            b_tip = header(b_rpc, FORK_B_BLOCKS)["hash"]
            b_first = header(b_rpc, 1)["hash"]
            b_deep = header(b_rpc, FORK_A_BLOCKS - 1)["hash"]
            if a_old_first == b_first or a_old_deep == b_deep:
                raise AssertionError("Regtest forks are not independent at deep history")
            if (info(a_rpc)["height"] != FORK_A_BLOCKS + 1 or
                    info(b_rpc)["height"] != FORK_B_BLOCKS + 1):
                raise AssertionError("Initial deep fork heights unexpected")
            print(
                f"PASS: native FAKECHAIN blocks on independent forks: "
                f"A={FORK_A_BLOCKS}, B={FORK_B_BLOCKS}, shared frozen genesis",
                flush=True,
            )
            # True native LMDB + read-only daemon RPC sampling; no made-up
            # monitor snapshots. Local processes are NOT independent operators.
            pre_observation = observe_real_nodes(
                a_rpc, b_rpc, time.monotonic() + max_seconds
            )
            pre_events, _ = assess_chain_risk(
                pre_observation, now=time.time(), alert_depth=3
            )
            pre_codes = {event.get("code") for event in pre_events}
            if "node_divergence" not in pre_codes or "node_height_gap" not in pre_codes:
                raise AssertionError(
                    "Real read-only observer failed to flag native competing forks"
                )
            print(
                "PASS: actual two-node read-only chain observer detected "
                "FAKECHAIN divergence and height gap before P2P convergence",
                flush=True,
            )
            # Native RandomX initialization is separate from P2P convergence;
            # do not count time spent mining toward the reorganization timeout.
            deadline = time.monotonic() + max_seconds

            # Offline mining cannot participate in P2P. Stop BOTH temporary
            # nodes and restart with P2P enabled, preserving their distinct
            # local FAKECHAIN LMDBs via --keep-fakechain. B accepts only local
            # incoming peers; A connects exclusively to B on loopback.
            for proc in procs:
                proc.terminate()
                proc.wait(timeout=10)
            for index, (node, pp, rp, peer) in enumerate((
                (b, b_p2p, b_rpc, None),
                (a, a_p2p, a_rpc, b_p2p),
            )):
                log = (home / (node.name + "-connected.log")).open("wb")
                logs.append(log)
                procs[1 if index == 0 else 0] = launch(
                    binary, node, pp, rp, log, peer=peer,
                )
                wait_ready(procs[1 if index == 0 else 0], rp, deadline)

            transient_rpc = wait_for_reorg(
                a_rpc, b_rpc, FORK_B_BLOCKS, b_tip, procs, deadline
            )
            if transient_rpc:
                print(
                    f"INFO: deep fork required {transient_rpc} bounded RPC retries; "
                    "final canonical checks still required", flush=True
                )
            if header(a_rpc, 1)["hash"] != b_first:
                raise AssertionError("Orphaned first fork is still canonical")
            if header(a_rpc, FORK_A_BLOCKS - 1)["hash"] != b_deep:
                raise AssertionError("Deep orphaned fork is still canonical")
            if header(a_rpc, FORK_A_BLOCKS - 1)["hash"] == a_old_deep:
                raise AssertionError("Old deep block survived reorg")
            if header(a_rpc, FORK_A_BLOCKS)["hash"] == a_old_tip:
                raise AssertionError("Original shorter fork tip remained canonical")
            if header(a_rpc, 0)["hash"] != a0:
                raise AssertionError("Genesis changed during reorganization")
            print(
                f"PASS: native FAKECHAIN P2P reorg displaced {FORK_A_BLOCKS} "
                f"formerly canonical blocks; B reached height {FORK_B_BLOCKS}",
                flush=True,
            )
            post_observation = observe_real_nodes(
                a_rpc, b_rpc, time.monotonic() + max_seconds
            )
            post_events, _ = assess_chain_risk(
                post_observation, previous=pre_observation,
                now=time.time(), alert_depth=3
            )
            if any(event.get("code") in ("node_divergence", "node_height_gap")
                   for event in post_events):
                raise AssertionError(
                    "Read-only observer still reports divergent canonical nodes after reorg"
                )
            reorg_alerts = [
                event for event in post_events
                if (event.get("node") == "fork-a"
                    and event.get("code") == "observed_reorg"
                    and event.get("minimum_depth", 0) >= FORK_A_BLOCKS
                    and event.get("severity") == "critical")
            ]
            if not reorg_alerts:
                raise AssertionError(
                    "Read-only observer missed genuine 66-deep canonical hash replacement"
                )
            print(
                "PASS: read-only chain observer flagged critical 66-block "
                "history replacement and confirmed final node convergence",
                flush=True,
            )

            # The *same compiled daemon* must still refuse public mainnet
            # mining; the independent mainnet CI smoke tests prove that path.
            print("PASS: regtest-specific block production; no mainnet mining or payouts", flush=True)
        except Exception:
            for path in (home / "fork-a.log", home / "fork-a-connected.log",
                         home / "fork-b.log", home / "fork-b-connected.log"):
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
