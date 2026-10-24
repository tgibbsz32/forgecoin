"""Opt-in real candidate capture; creates and removes its own disposable state.

Never uses an existing wallet/database. No mining, submission, or payout calls.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from urllib.request import Request

from .capture_template import capture, local_opener
from .isolated_daemon import offline_daemon_args


def rpc(port, method, params=None):
    body = json.dumps({"jsonrpc": "2.0", "id": "isolated-evidence",
                       "method": method, "params": params or {}}).encode()
    req = Request(f"http://127.0.0.1:{port}/json_rpc", body,
                  {"Content-Type": "application/json"})
    with local_opener().open(req, timeout=3) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError("Candidate RPC rejected evidence request")
    return result["result"]


def run(daemon, wallet, output, ports=(49581, 49580, 49582)):
    daemon, wallet = Path(daemon).resolve(), Path(wallet).resolve()
    if not wallet.is_file() or wallet.name.lower() not in {"forge-wallet-cli", "forge-wallet-cli.exe"}:
        raise ValueError("explicit candidate wallet CLI required")
    # Fail before creating a wallet if any requested service port is occupied.
    for port in ports:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", port))
    with tempfile.TemporaryDirectory(prefix="forgecoin-pool-") as temporary:
        root = Path(temporary)
        config = root / "empty.conf"
        config.write_text("", encoding="utf-8")
        wallet_path = root / "disposable"
        password = root / "password"
        password.write_text(os.urandom(32).hex(), encoding="ascii")
        command = [str(wallet), "--offline", "--no-dns", "--config-file", str(config),
                   "--generate-new-wallet", str(wallet_path), "--password-file", str(password),
                   "--mnemonic-language", "English", "--create-address-file",
                   "--shared-ringdb-dir", str(root / "ringdb"),
                   "--log-file", str(root / "wallet.log"), "--command", "exit"]
        # Wallet stdout contains secrets. Keep it out of terminal, reports and repository.
        created = subprocess.run(command, input=b"", stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, cwd=root, timeout=60)
        if created.returncode:
            raise RuntimeError(f"Disposable wallet creation failed ({created.returncode})")
        address = Path(str(wallet_path) + ".address.txt").read_text().strip()
        argv = offline_daemon_args(daemon, root / "data", *ports)
        argv += ["--config-file", str(config), "--log-file", str(root / "daemon.log")]
        with (root / "console.log").open("wb") as log:
            process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=log, stderr=log,
                                       cwd=root, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                deadline = time.monotonic() + 45
                while True:
                    if process.poll() is not None:
                        raise RuntimeError("Isolated daemon exited before RPC readiness")
                    try:
                        info = rpc(ports[0], "get_info")
                        break
                    except (OSError, ValueError):
                        if time.monotonic() >= deadline:
                            raise RuntimeError("Isolated RPC readiness timeout")
                        time.sleep(0.2)
                if not info.get("offline") or info["height"] != 1:
                    raise RuntimeError("Expected offline fresh genesis database")
                if info["incoming_connections_count"] or info["outgoing_connections_count"]:
                    raise RuntimeError("Unexpected peer connections")
                genesis = rpc(ports[0], "get_block_header_by_height", {"height": 0})["block_header"]["hash"]
                summary = capture(f"http://127.0.0.1:{ports[0]}/json_rpc", address, root / "summary.json")
                evidence = {"kind": "real-candidate-offline-template", "genesis_hash": genesis,
                            "daemon_sha256": hashlib.sha256(daemon.read_bytes()).hexdigest(),
                            "wallet_cli_sha256": hashlib.sha256(wallet.read_bytes()).hexdigest(),
                            "offline": info["offline"], "incoming_connections": 0,
                            "outgoing_connections": 0, "template": summary}
            finally:
                if process.poll() is None:
                    try:
                        process.communicate(b"exit\n", timeout=20)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()
                if process.stdin:
                    process.stdin.close()
            if process.returncode != 0:
                raise RuntimeError(f"Daemon shutdown was not clean ({process.returncode})")
        evidence["daemon_exit_code"] = process.returncode
    # Publish only after clean shutdown and disposable-state deletion.
    Path(output).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daemon", required=True)
    parser.add_argument("--wallet-cli", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.daemon, args.wallet_cli, args.output)
    print("Validated real offline candidate template; disposable state removed.")
