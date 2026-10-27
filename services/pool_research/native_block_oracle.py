"""Fail-closed adapter to the opt-in, offline ForgeCoin native block hashing oracle.

It parses a full CryptoNote block and rederives the consensus hashing blob.
No daemon RPC, wallet signing, share credits, mining or network access.
"""
from pathlib import Path
import re
import subprocess


class NativeBlockError(ValueError):
    pass


def native_hashing_blob(executable, full_blob: bytes, *, timeout: int = 15) -> bytes:
    if not isinstance(full_blob, bytes) or not 1 <= len(full_blob) <= 262144:
        raise NativeBlockError("invalid full block size")
    if type(timeout) is not int or not 1 <= timeout <= 30:
        raise NativeBlockError("invalid native timeout")
    try:
        path = Path(executable).resolve(strict=True)
        if not path.is_file():
            raise NativeBlockError("missing native block oracle")
        result = subprocess.run(
            [str(path)], input=full_blob.hex() + "\n", text=True,
            capture_output=True, timeout=timeout, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired, TypeError, ValueError) as exc:
        raise NativeBlockError("native block oracle unavailable") from exc
    if result.returncode != 0:
        raise NativeBlockError("native block parser rejected candidate")
    output = result.stdout.splitlines()
    if len(output) != 2 or any(
        not re.fullmatch(r"[0-9a-f]{2,524288}", line) or len(line) % 2
        for line in output
    ):
        raise NativeBlockError("invalid native block oracle response")
    if bytes.fromhex(output[0]) != full_blob:
        raise NativeBlockError("native block serialization differs from candidate")
    hashing = bytes.fromhex(output[1])
    if not 40 <= len(hashing) <= 262144:
        raise NativeBlockError("invalid native hashing blob length")
    return hashing
