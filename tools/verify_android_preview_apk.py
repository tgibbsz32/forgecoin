#!/usr/bin/env python3
"""Fail-closed offline check for the *non-mining* ForgeCoin Android UI preview.

This does not attest to APK signatures, consensus safety or wallet operations.
Never use its result as authorization to publish a mainnet mining APK.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from zipfile import BadZipFile, ZipFile

APPROVED_LIBS = {
    "lib/arm64-v8a/libforge_randomx.so",
    "lib/arm64-v8a/libforge_runtime_probe.so",
}
FORBIDDEN_TOKENS = (
    "libforged.so", "forge-wallet-rpc", "forge-wallet-cli",
    "forged.exe", "minerd", "wallet.keys", "private_key", "seed.txt",
)


def verify(apk: Path) -> dict:
    if not apk.is_file():
        raise ValueError(f"Missing Android debug preview APK: {apk}")
    size = apk.stat().st_size
    if size < 100000 or size > 50_000_000:
        raise ValueError("Unusual APK size: refusing to certify preview")
    sha256 = hashlib.sha256(apk.read_bytes()).hexdigest()
    try:
        with ZipFile(apk) as archive:
            names = archive.namelist()
            if archive.testzip() is not None:
                raise ValueError("APK archive contains a corrupt file")
    except (BadZipFile, OSError) as exc:
        raise ValueError("Invalid APK ZIP") from exc
    if not names or len(names) != len(set(names)):
        raise ValueError("APK entries missing or duplicated")
    if "AndroidManifest.xml" not in names or "classes.dex" not in names:
        raise ValueError("APK is missing Android entrypoint metadata")
    libraries = {n for n in names if n.startswith("lib/") and n.endswith(".so")}
    if libraries != APPROVED_LIBS:
        raise ValueError(f"Unexpected or missing native libraries: {sorted(libraries ^ APPROVED_LIBS)}")
    forbidden = [n for n in names if any(token in n.lower() for token in FORBIDDEN_TOKENS)]
    if forbidden:
        raise ValueError(f"Forbidden daemon/wallet/secret material bundled in UI preview: {forbidden[:8]}")
    for n in names:
        if n.startswith("/") or "\\..\\" in n or "/../" in n or n.startswith("../"):
            raise ValueError("Unsafe APK entry path")
    return {
        "artifact": str(apk),
        "classification": "restricted-debug-ui-preview-not-a-wallet-or-miner",
        "size_bytes": size,
        "sha256": sha256,
        "arm64_support_libraries": sorted(libraries),
        "native_daemon_included": False,
        "mainnet_release_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.apk)
    except (ValueError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
