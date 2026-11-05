#!/usr/bin/env python3
"""Verify the approved upstream XMRig archive before any extraction or bundling.

This verifies archive integrity against the published digest, not code signing,
driver safety, redistribution compliance or miner runtime behavior.
"""
import argparse
import hashlib
from pathlib import Path

ASSET = "xmrig-6.26.0-windows-x64.zip"
SHA256 = "bba8097cb37d9b458a1cb1137876b27cde6740d17fe4ccbc086ba07d87d9e147"


def verify(path: Path) -> str:
    if path.name != ASSET:
        raise ValueError(f"Unexpected asset name: {path.name!r}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != SHA256:
        raise ValueError(f"XMRig archive SHA-256 mismatch: {actual}")
    return actual


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    try:
        print(f"PASS: upstream XMRig archive SHA-256 {verify(args.archive)}")
    except (ValueError, OSError) as exc:
        parser.exit(1, f"FAIL: {exc}\n")
