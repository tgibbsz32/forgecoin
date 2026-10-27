"""Offline block reconstruction using the pinned native consensus helper.

Writes private evidence only. Does not mine, connect to RPC, or submit blocks.
"""
import argparse
import json
from pathlib import Path

from services.pool_research.reserve_candidate import build_reserve_candidate
from services.pool_research.template_adapter import validate_template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--helper", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--reserve", default="0102030405060708")
    args = parser.parse_args()
    if args.capture.resolve() == args.output.resolve():
        raise ValueError("refusing to overwrite source capture")
    if args.capture.stat().st_size > 1048576:
        raise ValueError("source capture too large")
    if len(args.reserve) != 16 or any(c not in "0123456789abcdefABCDEF" for c in args.reserve):
        raise ValueError("reserve requires eight hex bytes")
    with args.capture.open(encoding="utf-8") as file:
        source = validate_template(json.load(file))
    if source.height != 1 or source.difficulty != 1 or source.reserve_size != 8:
        raise ValueError("only isolated height-1 difficulty-1 reserve-8 template allowed")
    candidate = build_reserve_candidate(source, bytes.fromhex(args.reserve),
                                        args.helper, args.sha256)
    result = {
        "height": source.height, "difficulty": source.difficulty,
        "blocktemplate_blob": candidate.full_block_blob.hex(),
        "blockhashing_blob": candidate.hashing_blob.hex(),
        "reserved_offset": candidate.reserve_offset,
        "reserve_hex": candidate.reserve_bytes.hex(),
    }
    with args.output.open("x", encoding="utf-8") as file:
        json.dump({"result": result}, file, separators=(",", ":"))
    print("PASS: native coinbase-reserve/tree-root candidate reconstructed offline")


if __name__ == "__main__":
    main()
