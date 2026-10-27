"""Create a private header-nonce-only ForgeCoin candidate from captured RPC data.

No daemon, wallet, miner or network access. Output contains full block blobs;
keep it in a disposable private directory and never commit it.
"""
import argparse
import json
from pathlib import Path

from services.pool_research.nonce_candidate import build_nonce_candidate
from services.pool_research.template_adapter import validate_template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--nonce", default="01020304")
    args = parser.parse_args()

    if args.capture.resolve() == args.output.resolve():
        raise ValueError("refusing to overwrite original captured template")
    if args.capture.stat().st_size > 1024 * 1024:
        raise ValueError("capture exceeds size limit")
    with args.capture.open(encoding="utf-8") as source:
        raw = json.load(source)
    template = validate_template(raw)
    if template.height != 1 or template.difficulty != 1:
        raise ValueError("only isolated height-1 difficulty-1 test permitted")
    candidate = build_nonce_candidate(template, args.nonce)
    result = dict(raw["result"])
    result["blocktemplate_blob"] = candidate.full_block_blob.hex()
    result["blockhashing_blob"] = candidate.hashing_blob.hex()
    result["nonce_offset"] = candidate.nonce_offset
    result["nonce_hex"] = candidate.nonce.hex()
    # The output is intended for offline native verification and a single
    # explicitly requested private daemon submission, never public RPC.
    with args.output.open("x", encoding="utf-8") as output:
        json.dump({"result": result}, output, separators=(",", ":"))
    print("PASS: height=1 difficulty=1 header nonce modified in both blobs")


if __name__ == "__main__":
    main()
