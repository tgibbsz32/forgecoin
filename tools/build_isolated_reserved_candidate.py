"""Generate a private height-one, difficulty-one coinbase-reserve test candidate.

No daemon, miner, wallet, network access, share credit, or payouts.
Full candidate blobs are private disposable evidence: never add to Git.
"""
import argparse
import json
from pathlib import Path

from services.pool_research.reserved_candidate import build_reserved_candidate
from services.pool_research.template_adapter import validate_template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--nonce", default="01020304")
    parser.add_argument("--reserve", default="1122334455667788")
    args = parser.parse_args()
    if args.capture.resolve() == args.output.resolve():
        raise ValueError("refusing to overwrite captured template")
    if args.capture.stat().st_size > 1024*1024:
        raise ValueError("template capture exceeds one megabyte")
    with args.capture.open(encoding="utf-8") as f:
        source = json.load(f)
    template = validate_template(source)
    candidate = build_reserved_candidate(template, nonce_hex=args.nonce,
                                         reserve_hex=args.reserve)
    result = dict(source["result"])
    result.update({
        "blocktemplate_blob": candidate.full_block_blob.hex(),
        "blockhashing_blob": candidate.hashing_blob.hex(),
        "nonce_offset": candidate.nonce_offset,
        "nonce_hex": args.nonce.lower(),
        "reserve_hex": args.reserve.lower(),
    })
    with args.output.open("x", encoding="utf-8") as f:
        json.dump({"result": result}, f, separators=(",", ":"))
    print("PASS: isolated coinbase reserve, nonce and transaction tree root reconstructed")
    print(f"height={template.height} difficulty={template.difficulty} credited=0")


if __name__ == "__main__":
    main()
