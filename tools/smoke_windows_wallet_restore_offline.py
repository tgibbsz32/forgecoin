#!/usr/bin/env python3
"""Strictly local Windows wallet RPC create -> seed -> restore -> restart QA.

No daemon, mining, peer, external DNS, transfers, or public wallet files.
Creates disposable wallets ONLY in an OS-managed temporary directory.
Verifies pinned candidate bytes and a frozen launch lock first.
Does not print or persist seeds, passwords, private keys or wallet addresses.
This is candidate-binary validation, NOT production wallet release acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import (Request, ProxyHandler, HTTPPasswordMgrWithDefaultRealm,
                            HTTPDigestAuthHandler, build_opener)


REPO = Path(__file__).resolve().parents[1]
FROZEN_GENESIS = "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"
FROZEN_UUID = "bd936359-09e4-4fdb-8ec0-12fa9d6ef090"
PIN_RE = re.compile(r"^[0-9a-f]{64}$")
ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{90,140}$")
MAX_REPLY = 200_000
REQUEST_TIMEOUT = 3
RPC_AUTH: tuple[str, str] | None = None  # ephemeral, process-local QA only


class WalletRpcUnverified(Exception):
    pass


def verify_candidate(wallet_binary: Path, manifest_path: Path) -> None:
    if os.name != "nt" or not wallet_binary.is_file():
        raise WalletRpcUnverified("Windows candidate binary unavailable")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("release_authorized") is not False
            or manifest.get("genesis_nonce") != 20261026
            or manifest.get("genesis_hash") != FROZEN_GENESIS
            or manifest.get("network_uuid") != FROZEN_UUID
            or manifest.get("pool", {}).get("payouts_enabled") is not False
            or manifest.get("pool", {}).get("stratum_public") is not False):
        raise WalletRpcUnverified("Prelaunch chain or release locks changed")
    pin = manifest.get("windows_prelaunch_binaries_sha256", {}).get("forge-wallet-rpc.exe")
    if not isinstance(pin, str) or not PIN_RE.fullmatch(pin):
        raise WalletRpcUnverified("Candidate Windows wallet checksum pin missing")
    digest = hashlib.sha256()
    with wallet_binary.open("rb") as data:
        for chunk in iter(lambda: data.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != pin:
        raise WalletRpcUnverified("Candidate wallet binary did not match frozen pin")


def free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def rpc(port: int, method: str, params: dict | None = None, *,
        timeout: float = REQUEST_TIMEOUT) -> dict:
    data = json.dumps({
        "jsonrpc": "2.0", "id": "disposable-local-qa",
        "method": method, "params": params or {},
    }, separators=(",", ":")).encode("utf-8")
    req = Request(f"http://127.0.0.1:{port}/json_rpc", data=data,
                  headers={"Content-Type": "application/json"}, method="POST")
    if RPC_AUTH is None:
        raise WalletRpcUnverified("Authenticated wallet RPC has no credentials")
    login, secret = RPC_AUTH
    manager = HTTPPasswordMgrWithDefaultRealm()
    manager.add_password(None, f"http://127.0.0.1:{port}/", login, secret)
    opener = build_opener(ProxyHandler({}), HTTPDigestAuthHandler(manager))
    with opener.open(req, timeout=timeout) as response:
        bounded = response.read(MAX_REPLY + 1)
    if len(bounded) > MAX_REPLY:
        raise WalletRpcUnverified("Wallet RPC response too large")
    parsed = json.loads(bounded)
    if not isinstance(parsed, dict) or parsed.get("error"):
        raise WalletRpcUnverified("Native wallet RPC rejected request (details withheld)")
    result = parsed.get("result")
    if not isinstance(result, dict):
        raise WalletRpcUnverified("Invalid native wallet RPC result")
    return result


def unauthenticated_request_is_denied(port: int) -> None:
    req = Request(f"http://127.0.0.1:{port}/json_rpc",
                  data=b'{"jsonrpc":"2.0","id":"unauth","method":"get_version","params":{}}',
                  headers={"Content-Type": "application/json"}, method="POST")
    try:
        with build_opener(ProxyHandler({})).open(req, timeout=3) as response:
            if response.status == 200:
                raise WalletRpcUnverified("Unauthenticated wallet RPC unexpectedly accessible")
            raise WalletRpcUnverified("Wallet RPC returned unexpected unauthenticated status")
    except HTTPError as error:
        if error.code != 401:
            raise WalletRpcUnverified("Wallet RPC did not require digest authentication")


def wait_ready(process: subprocess.Popen, port: int, deadline: float) -> None:
    last_type, last_code = "none", "none"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise WalletRpcUnverified("Wallet RPC process exited before ready")
        try:
            rpc(port, "get_version", timeout=1.5)
            return
        except Exception as exc:
            last_type = type(exc).__name__
            last_code = str(getattr(exc, "code", "none"))
            time.sleep(0.25)
    raise WalletRpcUnverified("Loopback wallet RPC readiness timeout; "
                              "last exception class=" + last_type +
                              ", HTTP status=" + last_code)


def launch(binary: Path, home: Path, wallet_dir: Path,
           rpc_port: int, dead_daemon_port: int) -> subprocess.Popen:
    global RPC_AUTH
    login = "frgqa" + secrets.token_hex(6)
    secret = secrets.token_urlsafe(32)
    RPC_AUTH = (login, secret)
    # Only this disposable temp directory stores the RPC authentication
    # line; process arguments contain a private path, not the password.
    cfg = home / "private-wallet-auth.conf"
    if cfg.exists():
        raise WalletRpcUnverified("Stale wallet credentials file")
    with cfg.open("x", encoding="utf-8") as fh:
        fh.write("rpc-login=" + login + ":" + secret + "\n")
    # Explicit, never-public endpoints. The daemon intentionally does not
    # exist: no genesis block or outgoing peer can be mined in this test.
    args = [
        str(binary),
        "--wallet-dir", str(wallet_dir),
        "--daemon-address", f"127.0.0.1:{dead_daemon_port}",
        "--rpc-bind-ip", "127.0.0.1",
        "--rpc-bind-port", str(rpc_port),
        "--config-file", str(cfg),  # fail closed: digest auth is mandatory
        "--no-dns",
        "--no-initial-sync",
        "--log-level", "0",
        "--log-file", str(home / "private-wallet-rpc.log"),
    ]
    return subprocess.Popen(
        args, cwd=str(home), stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def stop(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def public_address(r: dict) -> str:
    address = r.get("address")
    if not isinstance(address, str) or not ADDRESS_RE.fullmatch(address):
        raise WalletRpcUnverified("Native wallet returned invalid public address")
    return address


def run(candidate: Path, manifest_path: Path, max_seconds: int) -> None:
    if not 20 <= max_seconds <= 90:
        raise WalletRpcUnverified("Timeout not within QA limits")
    verify_candidate(candidate, manifest_path)
    port, dead_port = free_loopback_port(), free_loopback_port()
    if port == dead_port:
        raise WalletRpcUnverified("Port collision")
    # No user-supplied wallet directory is ever accepted. The TemporaryDirectory
    # lifetime ends after wallet RPC is terminated on both success and failure.
    with tempfile.TemporaryDirectory(prefix="frg-native-win-wallet-qa-") as tmp:
        home = Path(tmp)
        wallet_dir = home / "wallets"
        wallet_dir.mkdir()
        process = None
        deadline = time.monotonic() + max_seconds
        password = secrets.token_urlsafe(28)
        original_address = None
        try:
            process = launch(candidate, home, wallet_dir, port, dead_port)
            wait_ready(process, port, deadline)
            unauthenticated_request_is_denied(port)
            (home / "private-wallet-auth.conf").unlink()
            print("PASS: private Windows wallet RPC rejected unauthenticated requests and accepted HTTP Digest only")
            rpc(port, "create_wallet", {
                "filename": "disposable_qa_original",
                "password": password, "language": "English",
            }, timeout=10)
            original_address = public_address(
                rpc(port, "get_address", {"account_index": 0}))
            keys = rpc(port, "query_key", {"key_type": "mnemonic"})
            seed = keys.get("key")
            if (not isinstance(seed, str) or
                    len(seed.split()) != 25 or len(seed) > 2048):
                raise WalletRpcUnverified("Native wallet did not provide 25-word seed")
            rpc(port, "close_wallet")
            print("PASS: pinned Windows native wallet RPC created a disposable 25-word wallet "
                  "on local loopback without a daemon or mining")

            # Native restore is the same method the GUI is now wired to.
            result = rpc(port, "restore_deterministic_wallet", {
                "filename": "disposable_qa_restored",
                "password": password,
                "seed": seed,
                "restore_height": 0,
                "language": "English",
            }, timeout=20)
            if public_address(result) != original_address:
                raise WalletRpcUnverified("Restored wallet address did not match")
            if public_address(rpc(port, "get_address",
                                  {"account_index": 0})) != original_address:
                raise WalletRpcUnverified("Opened restored wallet address mismatch")
            print("PASS: native restore_deterministic_wallet recovered the "
                  "same public address without broadcasting or mining")
            seed = None
            keys = None
            rpc(port, "close_wallet")
            try:
                rpc(port, "open_wallet", {
                    "filename": "disposable_qa_restored",
                    "password": "deliberately-incorrect-qa-password",
                }, timeout=5)
            except WalletRpcUnverified:
                pass
            else:
                raise WalletRpcUnverified("Wrong password unexpectedly opened wallet")
            rpc(port, "open_wallet", {
                "filename": "disposable_qa_restored", "password": password,
            }, timeout=10)
            if public_address(rpc(port, "get_address",
                                  {"account_index": 0})) != original_address:
                raise WalletRpcUnverified("Wallet failed to reopen from disk")
            rpc(port, "close_wallet")
            stop(process)
            process = None
            process = launch(candidate, home, wallet_dir, port, dead_port)
            wait_ready(process, port, deadline)
            unauthenticated_request_is_denied(port)
            (home / "private-wallet-auth.conf").unlink()
            rpc(port, "open_wallet", {
                "filename": "disposable_qa_restored", "password": password,
            }, timeout=10)
            if public_address(rpc(port, "get_address",
                                  {"account_index": 0})) != original_address:
                raise WalletRpcUnverified("Restored address changed on RPC restart")
            rpc(port, "close_wallet")
            print("PASS: native Windows wallet wrong-password rejection, "
                  "wallet disk reopen and RPC process restart preserved address")
            print("PASS: all wallet data disposable; no keys, seeds, addresses, "
                  "passwords, mining, Oracle or network peers accessed")
        finally:
            stop(process)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Disposable, no-mining native Windows FRG create/restore smoke")
    parser.add_argument("--wallet-rpc", type=Path, required=True)
    parser.add_argument("--manifest", type=Path,
                        default=REPO / "docs" / "mainnet.identity.json")
    parser.add_argument("--max-seconds", type=int, default=65)
    args = parser.parse_args()
    try:
        run(args.wallet_rpc.resolve(), args.manifest.resolve(), args.max_seconds)
    except Exception as exc:
        # Only our own deliberately sanitized error types can be displayed.
        # Never print service-provided text, any seed, secret or traceback.
        if type(exc) is WalletRpcUnverified:
            print("QA SAFE DIAGNOSTIC: " + str(exc), file=sys.stderr)
        else:
            print("QA SAFE DIAGNOSTIC: exception class " +
                  type(exc).__name__, file=sys.stderr)
        print("FAIL: native Windows offline wallet create/restore QA did not "
              "complete; no release acceptance claimed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
