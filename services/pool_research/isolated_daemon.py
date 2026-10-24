"""Build a disposable offline ForgeCoin daemon command. Does not execute."""
from pathlib import Path

def offline_daemon_args(executable, data_dir, rpc_port=49581, p2p_port=49580, zmq_port=49582):
    exe=Path(executable).resolve()
    root=Path(data_dir).resolve()
    if not exe.is_file() or exe.name.lower() not in {"forged.exe","forged"}:
        raise ValueError("explicit ForgeCoin daemon binary required")
    if not 1024 <= rpc_port <= 65535 or not 1024 <= p2p_port <= 65535 or not 1024 <= zmq_port <= 65535:
        raise ValueError("nonprivileged port required")
    if len({rpc_port,p2p_port,zmq_port})!=3:
        raise ValueError("ports must differ")
    if root.exists() and any(root.iterdir()):
        raise ValueError("data directory must be empty and disposable")
    return [str(exe),"--offline","--no-igd","--disable-dns-checkpoints",
            "--check-updates","disabled","--data-dir",str(root),
            "--rpc-bind-ip","127.0.0.1","--rpc-bind-port",str(rpc_port),
            "--p2p-bind-ip","127.0.0.1","--p2p-bind-port",str(p2p_port),
            "--zmq-rpc-bind-ip","127.0.0.1","--zmq-rpc-bind-port",str(zmq_port),
            ]
