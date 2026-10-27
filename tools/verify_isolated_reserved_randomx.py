"""Independent offline RandomX check for a private coinbase-reserved candidate.

The supplied trusted native worker verifies the RECONSTRUCTED hashing blob.
No RPC, mining, wallet, payout or public network interactions.
"""
import argparse
import json
from pathlib import Path

from services.pool_research.persistent_randomx import PersistentRandomXAdapter
from services.pool_research.pow_boundary import MAX_HASH
from services.pool_research.reserved_candidate import build_reserved_candidate
from services.pool_research.template_adapter import validate_template


def load(path):
    if path.stat().st_size > 1048576:
        raise ValueError("candidate evidence exceeds one megabyte")
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--worker", type=Path, required=True)
    args = parser.parse_args()
    template = validate_template(load(args.capture))
    output = load(args.candidate)["result"]
    candidate = build_reserved_candidate(template, nonce_hex=output["nonce_hex"],
                                         reserve_hex=output["reserve_hex"])
    if (candidate.full_block_blob.hex() != output["blocktemplate_blob"] or
            candidate.hashing_blob.hex() != output["blockhashing_blob"] or
            candidate.nonce_offset != output["nonce_offset"]):
        raise AssertionError("candidate does not match independently reconstructed template")
    worker = PersistentRandomXAdapter(args.worker, timeout=30)
    try:
        digest = worker(template.seed_hash, candidate.hashing_blob)
    finally:
        worker.close()
    if len(digest) != 32 or int.from_bytes(digest,"little") > MAX_HASH//template.difficulty:
        raise AssertionError("native RandomX failed network difficulty target")
    print("PASS: offline reserved coinbase+nonce reconstruction and native RandomX")
    print("height=%d difficulty=%d nonce_offset=%d credited=0" %
          (template.height, template.difficulty, candidate.nonce_offset))


if __name__ == "__main__":
    main()
