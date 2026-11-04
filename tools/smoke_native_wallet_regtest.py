#!/usr/bin/env python3
"""Native ForgeCoin wallet-RPC signing smoke on disposable localhost FAKECHAIN.

Testing ONLY: all wallets, keys, node DBs and RPC binds are freshly created in
a private tempdir. The mainnet mining/payout lock is never modified. No
pre-existing wallet, fee recipient, Oracle/VPS, bridge or public RPC is used.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

from smoke_native_pool_regtest import require_manifest
from smoke_regtest_reorg import FROZEN_GENESIS, header, info, launch, mine_in_batches, take_free_port, wait_ready

ROOT = Path(__file__).resolve().parents[1]
RX_HEX = re.compile(r"^[0-9a-fA-F]+$")


def wallet_rpc(port: int, method: str, params: dict | None = None) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": "wallet-lab",
                       "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/json_rpc", method="POST", data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=8) as response:
        raw = response.read(512001)
    if len(raw) > 512000:
        raise AssertionError("Wallet RPC response exceeded bounded test size")
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise AssertionError("Invalid wallet RPC JSON envelope")
    error = result.get("error")
    if error is not None:
        # RPC error may contain sensitive paths; never log the whole envelope.
        raise AssertionError(f"Native wallet RPC {method} failed with code "
                             f"{error.get('code') if isinstance(error, dict) else 'unknown'}")
    payload = result.get("result")
    if not isinstance(payload, dict):
        raise AssertionError(f"Native wallet RPC {method} did not return object")
    return payload


def wait_wallet(proc: subprocess.Popen, port: int, deadline: float) -> None:
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise AssertionError("Native wallet RPC executable exited before readiness")
        try:
            result = wallet_rpc(port, "get_version")
            if isinstance(result.get("version"), int) and result["version"] > 0:
                return
        except (OSError, TimeoutError, ValueError, AssertionError, urllib.error.URLError):
            pass
        time.sleep(0.5)
    raise AssertionError("Native wallet RPC did not become ready")


def must_public_address(value: object) -> str:
    if not isinstance(value, str) or not 90 <= len(value) <= 140:
        raise AssertionError("Invalid test-only wallet public address length")
    if not value[0].isalnum():
        raise AssertionError("Invalid test-only wallet address prefix")
    return value


def wait_wallet_height(wallet_port: int, wanted: int,
                       deadline: float) -> dict:
    last = None
    while time.monotonic() < deadline:
        wallet_rpc(wallet_port, "refresh")
        last = wallet_rpc(wallet_port, "get_height")
        if last.get("height") == wanted:
            return last
        time.sleep(0.7)
    raise AssertionError("Native wallet failed to synchronize FAKECHAIN block count")


def run(daemon_binary: Path, wallet_binary: Path, manifest: dict,
        max_seconds: int, *, signed_transfer: bool = False) -> None:
    if os.name == "nt":
        raise AssertionError("Use disposable Linux runner only")
    # A locked configuration is required even though the daemon is launched
    # FAKECHAIN only. No launch flag is accepted as a CLI argument.
    require_manifest(manifest)
    if manifest.get("genesis_hash") != FROZEN_GENESIS:
        raise AssertionError("Wrong frozen genesis identity")
    if not daemon_binary.is_file() or not wallet_binary.is_file():
        raise AssertionError("Native daemon or native wallet RPC missing")
    if not 30 <= max_seconds <= 240:
        raise AssertionError("Unbounded wallet integration test interval")

    used = {39481}
    chosen = []
    while len(chosen) < 3:
        p = take_free_port()
        if p not in used:
            chosen.append(p)
            used.add(p)
    p2p_port, daemon_port, wallet_port = chosen
    with tempfile.TemporaryDirectory(prefix="frg-native-wallet-FAKECHAIN-") as tmp:
        home = Path(tmp)
        node_dir, wallet_dir = home / "node", home / "wallets"
        node_dir.mkdir(mode=0o700)
        wallet_dir.mkdir(mode=0o700)
        daemon_log = (home / "native-daemon.log").open("wb")
        wallet_log = (home / "native-wallet.log").open("wb")
        processes: list[subprocess.Popen] = []
        try:
            node = launch(daemon_binary, node_dir, p2p_port, daemon_port,
                          daemon_log, offline=True)
            processes.append(node)
            deadline = time.monotonic() + max_seconds
            if (wait_ready(node, daemon_port, deadline).get("height") != 1 or
                    header(daemon_port, 0)["hash"] != FROZEN_GENESIS):
                raise AssertionError("Wallet test may only use disposable genesis-only FAKECHAIN")

            args = [
                str(wallet_binary.resolve()),
                "--wallet-dir", str(wallet_dir),
                "--daemon-address", f"127.0.0.1:{daemon_port}",
                "--rpc-bind-ip", "127.0.0.1",
                "--rpc-bind-port", str(wallet_port),
                "--disable-rpc-login",  # localhost ephemeral CI exclusively
                "--no-initial-sync", "--log-level", "0",
                "--log-file", str(home / "wallet-internal.log"),
            ]
            wallet_proc = subprocess.Popen(
                args, cwd=str(home), stdin=subprocess.DEVNULL,
                stdout=wallet_log, stderr=subprocess.STDOUT, close_fds=True,
                env={**os.environ, "HOME": str(home)},
            )
            processes.append(wallet_proc)
            wait_wallet(wallet_proc, wallet_port, deadline)

            # This password and the generated keys never appear in output.
            wallet_password = secrets.token_urlsafe(24)
            wallet_rpc(wallet_port, "create_wallet", {
                "filename": "disposable_regtest_source",
                "password": wallet_password, "language": "English",
            })
            created = wallet_rpc(wallet_port, "get_address", {"account_index": 0})
            address = must_public_address(created.get("address"))
            initial = wallet_rpc(wallet_port, "get_balance", {"account_index": 0})
            if initial.get("balance") != 0 or initial.get("unlocked_balance") != 0:
                raise AssertionError("Disposable wallet was not created empty")
            print("PASS: native wallet RPC created fresh private tempdir wallet and "
                  "returned public address; zero balance, localhost-only, no keys logged",
                  flush=True)

            # Mine only into the ephemeral generated wallet on FAKECHAIN.
            # A newly created wallet output at block 1 becomes spendable at 61+.
            mine_in_batches(daemon_port, address, 80, 83000)
            wanted_height = 81
            if info(daemon_port).get("height") != wanted_height:
                raise AssertionError("Disposable FAKECHAIN did not reach 80 mined blocks")
            wait_wallet_height(wallet_port, wanted_height,
                               time.monotonic() + max_seconds)
            funded = wallet_rpc(wallet_port, "get_balance", {"account_index": 0})
            if (not isinstance(funded.get("balance"), int)
                    or not isinstance(funded.get("unlocked_balance"), int)
                    or funded["unlocked_balance"] <= 0
                    or funded["unlocked_balance"] > funded["balance"]):
                raise AssertionError("Real native wallet did not discover spendable regtest reward")
            print("PASS: native wallet refreshed 80 genuine FAKECHAIN blocks and "
                  "recognized positive unlocked coinbase funds (no live FRG)", flush=True)

            if signed_transfer:
                # Recipient is a new subaddress of this same ephemeral wallet.
                recipient = wallet_rpc(wallet_port, "create_address",
                                       {"account_index": 0, "label": "test-only"})
                destination = must_public_address(recipient.get("address"))
                if destination == address:
                    raise AssertionError("Wallet returned identical primary and test subaddresses")
                transfer = wallet_rpc(wallet_port, "transfer", {
                    "destinations": [{"address": destination, "amount": 100_000_000}],
                    "account_index": 0, "priority": 1, "ring_size": 16,
                    "do_not_relay": True, "get_tx_hex": True, "get_tx_metadata": False,
                    "get_tx_key": False,
                })
                tx_hex = transfer.get("tx_blob")
                tx_hash = transfer.get("tx_hash")
                fee = transfer.get("fee")
                if (not isinstance(tx_hex, str) or len(tx_hex) < 180 or
                        len(tx_hex) % 2 or not RX_HEX.fullmatch(tx_hex) or
                        not isinstance(tx_hash, str) or len(tx_hash) != 64 or
                        not RX_HEX.fullmatch(tx_hash) or not isinstance(fee, int)
                        or fee <= 0):
                    raise AssertionError("Native wallet did not produce a serialized signed transfer")
                print("PASS: native wallet constructed signed 16-member-ring "
                      "serialized transfer; nonzero fee, no relay or wallet spending",
                      flush=True)
                # Intentionally DO NOT submit to any daemon or real network here.
                # A distinct, stricter test must validate native mempool receipt
                # and destination balance without weakening mainnet prelaunch.
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
            wallet_log.close()
            daemon_log.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", type=Path, required=True)
    parser.add_argument("--wallet", type=Path, required=True)
    parser.add_argument("--manifest", type=Path,
                        default=ROOT / "config/mainnet.identity.json")
    parser.add_argument("--max-seconds", type=int, default=120)
    parser.add_argument("--signed-transfer", action="store_true")
    args = parser.parse_args()
    run(args.daemon, args.wallet,
        json.loads(args.manifest.read_text(encoding="utf-8")),
        args.max_seconds, signed_transfer=args.signed_transfer)


if __name__ == "__main__":
    main()
