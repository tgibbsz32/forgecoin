"""Independent source-matched native cross-check of an isolated reserve/nonce block.

No daemon connections, mining, coins, wallets, credits, or payouts. The native
helper reconstructs the coinbase transaction tree root independently of the
Python research candidate builder. Raw blobs stay in private input captures.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path

from services.pool_research.nonce_candidate import build_nonce_candidate
from services.pool_research.reserve_candidate import build_reserve_candidate
from services.pool_research.template_adapter import validate_template


def read_json(path):
    if path.stat().st_size > 1048576:
        raise ValueError("oversized private evidence file")
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--helper", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()

    original = validate_template(read_json(args.capture))
    proposed = read_json(args.candidate)["result"]
    if original.height != 1 or original.difficulty != 1 or original.reserve_size != 8:
        raise ValueError("isolated height-one difficulty-one template required")
    reserve = bytes.fromhex(proposed["reserve_hex"])
    if len(reserve) != 8:
        raise ValueError("invalid reserved payload")

    native = build_reserve_candidate(original, reserve, args.helper, args.sha256)
    modified_template = replace(
        original, blocktemplate_blob=native.full_block_blob,
        blockhashing_blob=native.hashing_blob)
    with_nonce = build_nonce_candidate(modified_template, proposed["nonce_hex"])
    if (with_nonce.full_block_blob.hex() != proposed["blocktemplate_blob"]
            or with_nonce.hashing_blob.hex() != proposed["blockhashing_blob"]
            or with_nonce.nonce_offset != proposed["nonce_offset"]
            or original.reserved_offset != native.reserve_offset):
        raise AssertionError("native transaction root disagrees with independent candidate")
    print("PASS: source-matched C++ consensus root and Python reserve+nonce candidate agree")
    print("height=1 difficulty=1 credited=0; no network calls")


if __name__ == "__main__":
    main()
