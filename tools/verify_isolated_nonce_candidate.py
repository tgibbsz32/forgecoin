"""Offline native RandomX check of a nonce-modified captured block candidate.

This uses a supplied trusted native worker; no daemon, wallet, network access,
miner, share credit, or payout. Raw blobs/seeds are never printed.
"""
import argparse
import json
from pathlib import Path

from services.pool_research.nonce_candidate import build_nonce_candidate
from services.pool_research.persistent_randomx import PersistentRandomXAdapter
from services.pool_research.pow_boundary import MAX_HASH
from services.pool_research.template_adapter import validate_template


def load_json(path):
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("capture too large")
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--worker", required=True, type=Path)
    args = parser.parse_args()

    source = validate_template(load_json(args.capture))
    proposed = load_json(args.candidate)["result"]
    candidate = build_nonce_candidate(source, proposed["nonce_hex"])
    if (candidate.full_block_blob.hex() != proposed["blocktemplate_blob"] or
            candidate.hashing_blob.hex() != proposed["blockhashing_blob"] or
            candidate.nonce_offset != proposed["nonce_offset"]):
        raise AssertionError("candidate does not match original template and nonce")

    worker = PersistentRandomXAdapter(args.worker, timeout=30)
    try:
        digest = worker(source.seed_hash, candidate.hashing_blob)
    finally:
        worker.close()
    if len(digest) != 32:
        raise AssertionError("invalid RandomX worker digest")
    if int.from_bytes(digest, "little") > MAX_HASH // source.difficulty:
        raise AssertionError("modified candidate does not meet network difficulty")
    print("PASS: exact nonce-only reconstruction, native RandomX and network target")
    print("height=%d difficulty=%d nonce_offset=%d credited=0" %
          (source.height, source.difficulty, candidate.nonce_offset))


if __name__ == "__main__":
    main()
