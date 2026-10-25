#!/usr/bin/env python3
"""Read-only FCMP++ source-migration inventory. This is NOT a cryptography audit.

Usage:
  python tools/fcmp_port_preflight.py --fork-root .
  python tools/fcmp_port_preflight.py --fork-root . --upstream-root PATH
  python tools/fcmp_port_preflight.py --fork-root . --require-integrated

The optional upstream checkout MUST match the pinned, reviewed beta v3.1
commit. An incomplete fork returns exit 2 only when --require-integrated is set.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

REFERENCE_URL = "https://github.com/seraphis-migration/monero"
REFERENCE_TAG = "v0.19.0.0-beta.3.1"
REFERENCE_COMMIT = "d80596ad18110390b6ca97a77e29aba36f4644c9"


@dataclass(frozen=True)
class Surface:
    name: str
    path: str
    marker: str = ""


# Broad markers indicate presence, NOT correct cryptographic integration.
SURFACES = (
    Surface("Rust FCMP++ proof backend", "src/fcmp_pp/fcmp_pp_rust/src/lib.rs", "verify"),
    Surface("FCMP++ C++ binding", "src/fcmp_pp/fcmp_pp_crypto.cpp", "fcmp"),
    Surface("FCMP++ build integration", "src/fcmp_pp/CMakeLists.txt"),
    Surface("Curve-tree membership accumulator", "src/fcmp_pp/curve_trees.cpp", "Curve"),
    Surface("CARROT scanning", "src/carrot_core/scan.cpp", "carrot"),
    Surface("FCMP++ transaction format", "src/ringct/rctTypes.h", "RCTTypeFcmpPlusPlus"),
    Surface("FCMP++ consensus verifier", "src/cryptonote_core/blockchain.cpp", "HF_VERSION_FCMP_PLUS_PLUS"),
    Surface("Persistent tree DB", "src/blockchain_db/lmdb/db_lmdb.cpp", "fcmp"),
    Surface("FCMP++ wallet migration", "src/wallet/wallet2.cpp", "fcmp"),
    Surface("Fork-gated block serialization", "src/cryptonote_basic/cryptonote_basic.h", "fcmp_pp_tree_root"),
    Surface("FCMP++ unit tests", "tests/unit_tests/fcmp_pp.cpp"),
)


def inspect(root: Path) -> dict[str, object]:
    surfaces: list[dict[str, object]] = []
    for spec in SURFACES:
        file = root / spec.path
        exists = file.is_file()
        matched = False
        if exists:
            if spec.marker:
                # Bounded source read; no executables, wallet keys or external network.
                matched = spec.marker.lower() in file.read_text(
                    encoding="utf-8", errors="replace"
                ).lower()
            else:
                matched = True
        surfaces.append(
            {"name": spec.name, "path": spec.path, "present": bool(matched)}
        )
    return {
        "root": str(root.resolve()),
        "surfaces": surfaces,
        "present_count": sum(item["present"] for item in surfaces),
        "total_count": len(surfaces),
        "source_presence_complete": all(item["present"] for item in surfaces),
    }


def commit_of(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True, capture_output=True, check=False, timeout=20,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fork-root", type=Path, default=Path("."))
    parser.add_argument("--upstream-root", type=Path)
    parser.add_argument("--require-integrated", action="store_true")
    args = parser.parse_args(argv)
    if not args.fork_root.is_dir():
        parser.error("--fork-root must be a directory")
    report: dict[str, object] = {
        "kind": "FCMP++ read-only migration presence inventory",
        "not_an_audit": True,
        "not_a_release_approval": True,
        "reference": {
            "url": REFERENCE_URL,
            "tag": REFERENCE_TAG,
            "commit": REFERENCE_COMMIT,
        },
        "fork": inspect(args.fork_root),
    }
    exit_code = 0
    if args.upstream_root:
        if not args.upstream_root.is_dir():
            parser.error("--upstream-root must be a directory")
        commit = commit_of(args.upstream_root)
        reference = inspect(args.upstream_root)
        reference["actual_commit"] = commit
        reference["pinned_commit_matches"] = commit == REFERENCE_COMMIT
        report["reference_checkout"] = reference
        if commit != REFERENCE_COMMIT or not reference["source_presence_complete"]:
            exit_code = 3
    if args.require_integrated and not report["fork"]["source_presence_complete"]:
        exit_code = 2
    print(json.dumps(report, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
