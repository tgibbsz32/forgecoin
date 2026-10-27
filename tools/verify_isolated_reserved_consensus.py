"""Cross-check isolated coinbase reconstruction with source-matched native parsing.

Explicit offline invocation only. Reads a private captured height-1 template,
uses no RPC, and does not write any candidate blocks or expose wallet data.
"""
import argparse
import json
from pathlib import Path

from services.pool_research.native_block_oracle import native_hashing_blob
from services.pool_research.reserved_candidate import build_reserved_candidate
from services.pool_research.template_adapter import validate_template


def verify(capture: Path, native_executable: Path):
    if capture.stat().st_size > 1048576:
        raise ValueError("private template exceeds permitted size")
    with capture.open(encoding="utf-8") as source:
        template = validate_template(json.load(source))
    if template.height != 1 or template.difficulty != 1 or template.reserve_size != 8:
        raise ValueError("disposable height-one, difficulty-one template required")
    if native_hashing_blob(native_executable, template.blocktemplate_blob) != template.blockhashing_blob:
        raise AssertionError("native source disagrees with original daemon template")

    reserve = bytes.fromhex("1122334455667788")
    nonce = "01020304"
    candidate = build_reserved_candidate(template, reserve_hex=reserve.hex(), nonce_hex=nonce)
    original = template.blocktemplate_blob
    edited = candidate.full_block_blob
    modified = {i for i, (before, after) in enumerate(zip(original, edited)) if before != after}
    expected_regions = (range(candidate.nonce_offset, candidate.nonce_offset + 4),
                        range(template.reserved_offset, template.reserved_offset + 8))
    if (len(original) != len(edited) or not modified or
            any(index not in expected_regions[0] and index not in expected_regions[1]
                for index in modified)):
        raise AssertionError("candidate changed bytes outside nonce and coinbase reserve")

    native = native_hashing_blob(native_executable, edited)
    if native != candidate.hashing_blob:
        raise AssertionError("candidate transaction-tree root differs from native consensus")
    if native == template.blockhashing_blob:
        raise AssertionError("coinbase edit failed to change native hashing blob")
    print("PASS: reserve and nonce reconstruction matches independent native consensus")
    print(f"height=1 difficulty=1 nonce_offset={candidate.nonce_offset} "
          f"reserve_offset={template.reserved_offset} credited=0")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--oracle", required=True, type=Path)
    args = parser.parse_args()
    verify(args.capture, args.oracle)


if __name__ == "__main__":
    main()
