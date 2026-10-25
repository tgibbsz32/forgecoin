#!/usr/bin/env python3
"""Read-only prerequisites for isolated desktop Solo/Pool acceptance tests."""
import argparse
import hashlib
import struct
from pathlib import Path

def inspect(path, label):
    if path is None:
        return "BLOCKED " + label + ": not supplied"
    p = Path(path)
    if not p.is_file():
        return "BLOCKED " + label + ": file missing"
    if p.stat().st_size == 0:
        return "BLOCKED " + label + ": empty file"
    with p.open("rb") as handle:
        header = handle.read(64)
        if len(header) < 64 or header[:2] != b"MZ":
            return "BLOCKED " + label + ": invalid DOS header"
        offset = struct.unpack_from("<I", header, 0x3C)[0]
        if offset < 64 or offset > p.stat().st_size - 24:
            return "BLOCKED " + label + ": invalid PE offset"
        handle.seek(offset)
        pe = handle.read(24)
        if len(pe) != 24 or pe[:4] != b"PE\\x00\\x00":
            return "BLOCKED " + label + ": invalid PE signature"
        machine = struct.unpack_from("<H", pe, 4)[0]
        if machine != 0x8664:
            return "BLOCKED " + label + ": expected Windows x64 executable"
    h = hashlib.sha256()
    with p.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "FOUND " + label + ": sha256=" + h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--desktop", type=Path)
    parser.add_argument("--daemon", type=Path)
    parser.add_argument("--wallet-rpc", type=Path)
    parser.add_argument("--xmrig", type=Path)
    args = parser.parse_args()
    states = [inspect(getattr(args, k.replace("-", "_")), k)
              for k in ("desktop", "daemon", "wallet-rpc", "xmrig")]
    for state in states:
        print(state)
    if any(state.startswith("BLOCKED") for state in states):
        print("NOT VALIDATED: do not run acceptance or approve desktop V1")
        return 1
    print("PREREQUISITES PRESENT ONLY: functional Solo/Pool tests still required")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
