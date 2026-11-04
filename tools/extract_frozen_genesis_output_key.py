#!/usr/bin/env python3
"""Read the PUBLIC genesis output key from the frozen 20261026 tx serialization.

No RPC, private key, wallet, network, database or transaction mutation.
Used only as input to the independent native signed-ring regression.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENESIS_HASH = "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"


def uvarint(data: bytes, start: int) -> tuple[int, int]:
    result = 0
    shift = 0
    index = start
    while index < len(data) and shift <= 63:
        octet = data[index]
        index += 1
        result |= (octet & 127) << shift
        if not octet & 128:
            if result > (1 << 64) - 1:
                raise ValueError("genesis varint exceeds uint64")
            if index - start > 1 and octet == 0:
                raise ValueError("noncanonical genesis varint")
            return result, index
        shift += 7
    raise ValueError("unterminated or oversized genesis varint")


def extract_genesis_pubkey(manifest: dict) -> str:
    if (manifest.get("genesis_nonce") != 20261026
            or manifest.get("genesis_hash") != GENESIS_HASH
            or manifest.get("genesis_height") != 0
            or manifest.get("mined_blocks_permitted_before_launch") != 0
            or manifest.get("release_authorized") is not False):
        raise ValueError("frozen genesis identity or release lock mismatch")
    hex_blob = manifest.get("genesis_tx_hex")
    if not isinstance(hex_blob, str) or not hex_blob or len(hex_blob) % 2:
        raise ValueError("invalid genesis transaction hex")
    try:
        data = bytes.fromhex(hex_blob)
    except ValueError as exc:
        raise ValueError("nonhex genesis serialization") from exc

    pos = 0
    version, pos = uvarint(data, pos)
    unlock, pos = uvarint(data, pos)
    input_count, pos = uvarint(data, pos)
    if pos >= len(data):
        raise ValueError("truncated genesis input")
    input_type = data[pos]
    pos += 1
    coinbase_height, pos = uvarint(data, pos)
    output_count, pos = uvarint(data, pos)
    amount, pos = uvarint(data, pos)
    if pos >= len(data):
        raise ValueError("truncated genesis output")
    target_type = data[pos]
    pos += 1
    if (version != 1 or unlock != 60 or input_count != 1 or
            input_type != 0xff or coinbase_height != 0 or
            output_count != 1 or target_type != 2 or
            amount != manifest.get("currency", {}).get("genesis_output_atomic")):
        raise ValueError("unexpected frozen genesis coinbase structure")
    if len(data) - pos < 32:
        raise ValueError("truncated genesis output public key")
    public_key = data[pos:pos + 32].hex()
    pos += 32
    extra_size, pos = uvarint(data, pos)
    if len(data) - pos != extra_size:
        raise ValueError("mismatched genesis extra length")
    return public_key


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path,
                        default=ROOT / "config/mainnet.identity.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    print(extract_genesis_pubkey(manifest))


if __name__ == "__main__":
    main()
