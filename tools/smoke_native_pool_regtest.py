#!/usr/bin/env python3
"""Disposable native C pool ↔ genuine ForgeCoin FAKECHAIN RPC smoke.

Research-only. Pool, daemon RPC/P2P and WebUI bind only 127.0.0.1; no
wallet process/keys, public mining, pool credits, transfer or Oracle access.
No prelaunch MAINNET block is mined. No persistent state outside tempdir.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

from smoke_regtest_reorg import (
    FROZEN_GENESIS, header, info, launch, mine, take_free_port, wait_ready,
)

ROOT = Path(__file__).resolve().parents[1]
POOL_CONFIG = ROOT / "services/official_pool/jtgrassie/pool.conf"
RPC_PORT = 39481  # frozen selected daemon RPC identity, REQUIRED by native C pool


def require_manifest(manifest: dict) -> str:
    pool = manifest.get("pool", {})
    if (manifest.get("release_authorized") is not False
            or manifest.get("genesis_hash") != FROZEN_GENESIS
            or manifest.get("mined_blocks_permitted_before_launch") != 0
            or manifest.get("consensus_guard_stage") != "draft-unbuilt"
            or manifest.get("ports", {}).get("daemon_rpc") != RPC_PORT
            or pool.get("payouts_enabled") is not False
            or pool.get("stratum_public") is not False
            or pool.get("operator_fee_fraction") != "0.01"):
        raise AssertionError("Only frozen, payout-locked prelaunch manifest is permitted")
    address = pool.get("operator_fee_address")
    if not isinstance(address, str) or not 90 <= len(address) <= 130:
        raise AssertionError("Valid-looking public FRG test destination missing")
    return address


def test_config(public_address: str, directory: Path, pool_port: int,
                web_port: int, unbound_wallet_port: int) -> Path:
    """Derive from reviewed pool template, forcibly overriding unsafe settings."""
    original = POOL_CONFIG.read_text(encoding="utf-8")
    parsed = {}
    for raw in original.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise AssertionError("Unexpected native pool config syntax")
        k, value = (v.strip() for v in line.split("=", 1))
        if k in parsed:
            raise AssertionError("Duplicate pool config key")
        parsed[k] = value

    overrides = {
        "pool-listen": "127.0.0.1", "webui-listen": "127.0.0.1",
        "pool-port": str(pool_port), "webui-port": str(web_port),
        "rpc-host": "127.0.0.1", "rpc-port": str(RPC_PORT),
        "wallet-rpc-host": "127.0.0.1",
        "wallet-rpc-port": str(unbound_wallet_port),  # no signer runs here
        "pool-wallet": public_address, "pool-fee-wallet": "",
        "pool-fee": "0.01", "forked": "0", "processes": "1",
        "pool-ssl-port": "", "disable-self-select": "1",
        "disable-hash-check": "0", "disable-payouts": "1",
        "log-file": "", "data-dir": str(directory),
        "pool-view-key": "0" * 64,  # dummy; never derive a private key
        "trusted-listen": "", "upstream-host": "",
    }
    if not all(k in parsed for k in (
            "pool-listen", "pool-port", "webui-listen", "webui-port",
            "rpc-host", "rpc-port", "wallet-rpc-host", "wallet-rpc-port",
            "pool-wallet", "pool-fee", "disable-self-select",
            "disable-hash-check", "disable-payouts", "forked", "processes",
            "data-dir")):
        raise AssertionError("Official pool config schema changed; refuse startup")
    parsed.update(overrides)
    if (parsed["pool-listen"] != "127.0.0.1"
            or parsed["webui-listen"] != "127.0.0.1"
            or parsed["rpc-host"] != "127.0.0.1"
            or parsed["disable-payouts"] != "1"
            or parsed["disable-hash-check"] != "0"
            or parsed["disable-self-select"] != "1"):
        raise AssertionError("Research pool safety contract changed")

    result = directory.parent / "pool-smoke.conf"
    result.write_text("".join(f"{k} = {v}\n" for k, v in parsed.items()),
                      encoding="utf-8")
    result.chmod(0o600)
    return result


def local_stats(port: int) -> dict:
    with urllib.request.urlopen(
        f"http://127.0.0.1:{port}/stats", timeout=3
    ) as response:
        if response.status != 200:
            raise AssertionError("Native pool WebUI returned non-200 status")
        raw = response.read(200_001)
    if len(raw) > 200_000:
        raise AssertionError("Native pool stats response too large")
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise AssertionError("Native pool stats is not JSON object")
    return result


def wait_stats(proc: subprocess.Popen, web_port: int, deadline: float,
               minimum_height: int, *, require_template: bool = False) -> dict:
    last = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise AssertionError("Native C pool exited during local-only smoke")
        try:
            last = local_stats(web_port)
            height = last.get("network_height")
            template_seen = last.get("last_template_fetched", 0)
            if (isinstance(height, int) and not isinstance(height, bool)
                    and height >= minimum_height
                    and (not require_template or
                         (isinstance(template_seen, int) and template_seen > 0
                          and last.get("network_difficulty") == 1))):
                return last
        except (OSError, ValueError, urllib.error.URLError):
            pass
        time.sleep(0.5)
    raise AssertionError(f"Native pool did not report height >= {minimum_height}; "
                         f"last stats: {last!r}")


def run(daemon_binary: Path, pool_binary: Path, manifest: dict,
        max_seconds: int) -> None:
    if os.name == "nt":
        raise SystemExit("Linux ephemeral runner only, never Windows/Oracle")
    if not daemon_binary.is_file() or not pool_binary.is_file():
        raise AssertionError("Missing verified native daemon or C pool")
    address = require_manifest(manifest)
    ports = []
    while len(ports) < 4:
        p = take_free_port()
        if p != RPC_PORT and p not in ports:
            ports.append(p)
    p2p_port, pool_port, web_port, wallet_port = ports
    with tempfile.TemporaryDirectory(prefix="frg-pool-fakechain-smoke-") as temp:
        root = Path(temp)
        node_dir, pool_dir = root / "node", root / "pool-data"
        node_dir.mkdir()
        pool_dir.mkdir()
        pool_conf = test_config(address, pool_dir, pool_port, web_port, wallet_port)
        logs = []
        processes = []
        try:
            for name in ("native-daemon.log", "native-pool.log"):
                logs.append((root / name).open("wb"))
            # A genuine isolated native FAKECHAIN node, never real MAINNET.
            node = launch(daemon_binary, node_dir, p2p_port, RPC_PORT,
                          logs[0], offline=True)
            processes.append(node)
            deadline = time.monotonic() + max_seconds
            before = wait_ready(node, RPC_PORT, deadline)
            if before.get("height") != 1 or header(RPC_PORT, 0)["hash"] != FROZEN_GENESIS:
                raise AssertionError("Wrong initial fakechain state")

            env = {k: v for k, v in os.environ.items()
                   if k != "MONERO_RANDOMX_FULL_MEM"}
            pool = subprocess.Popen(
                [str(pool_binary.resolve()), "--config-file", str(pool_conf)],
                cwd=str(root), stdin=subprocess.DEVNULL,
                stdout=logs[1], stderr=subprocess.STDOUT,
                close_fds=True, env=env,
            )
            processes.append(pool)
            # Pool WebUI reports zero-based canonical *tip index*, while
            # get_info.height counts genesis as block one.
            first = wait_stats(pool, web_port, deadline, 0, require_template=True)
            if (first.get("network_height") != 0
                    or first.get("pool_fee") != 0.01
                    or first.get("allow_self_select") != 0
                    or first.get("pool_blocks_found") != 0
                    or first.get("pool_port") != pool_port):
                raise AssertionError("Unsafe or incorrect native pool statistics")

            # Mine exactly one *FAKECHAIN* block directly in daemon.
            # This tests the pool's genuine header refresh, not share acceptance
            # and absolutely not wallet payout. Never use MAINNET here.
            mine(RPC_PORT, address, 1, 13)
            if info(RPC_PORT).get("height") != 2:
                raise AssertionError("Native fakechain did not accept its block")
            if pool.poll() is not None:
                raise AssertionError("Native pool stopped after fakechain block")
            os.kill(pool.pid, signal.SIGUSR1)  # native refresh callback
            # Require actual same-process transition of pool tip 0 -> 1.
            # This never confuses the daemon's block *count* 1 -> 2.
            after = wait_stats(pool, web_port, time.monotonic() + max_seconds, 1)
            if (after.get("network_height") != 1
                    or after.get("pool_fee") != 0.01
                    or after.get("pool_blocks_found") != 0):
                raise AssertionError("Native pool failed to observe the canonical FAKECHAIN tip")
            print("PASS: real native C pool/FAKECHAIN RPC and WebUI on localhost; "
                  "pool tip 0→1, daemon count 1→2, 1% fee, no wallet/payout",
                  flush=True)
        except Exception:
            for path in (root / "native-daemon.log", root / "native-pool.log"):
                if path.exists():
                    excerpt = path.read_text(encoding="utf-8", errors="replace").splitlines()[-45:]
                    print(f"DIAGNOSTIC {path.name}:\n" + "\n".join(excerpt)[-5000:],
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
    parser.add_argument("--manifest", type=Path,
                        default=ROOT / "config/mainnet.identity.json")
    parser.add_argument("--max-seconds", type=int, default=120)
    args = parser.parse_args()
    if not 30 <= args.max_seconds <= 240:
        raise SystemExit("Pool smoke timeout outside bounded CI-only interval")
    run(args.daemon, args.pool,
        json.loads(args.manifest.read_text(encoding="utf-8")), args.max_seconds)


if __name__ == "__main__":
    main()
