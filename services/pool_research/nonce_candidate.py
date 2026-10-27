"""Offline header-nonce candidate reconstruction for a native ForgeCoin template.

This modifies *only* the CryptoNote block-header nonce, not the coinbase
reserve, transaction tree, block rewards, or consensus configuration.
No daemon RPC or miner activity occurs here.
"""
from dataclasses import dataclass

from .pow_boundary import VerificationError
from .template_adapter import Template


@dataclass(frozen=True)
class NonceCandidate:
    nonce_offset: int
    nonce: bytes
    full_block_blob: bytes
    hashing_blob: bytes


def _read_varint(data: bytes, start: int) -> int:
    value = 0
    for index in range(10):
        pos = start + index
        if pos >= len(data):
            raise VerificationError("truncated block header")
        byte = data[pos]
        if index == 9 and byte > 1:
            raise VerificationError("header varint overflow")
        value |= (byte & 127) << (7 * index)
        if byte < 128:
            if index and value < (1 << (7 * index)):
                raise VerificationError("noncanonical header varint")
            return pos + 1
    raise VerificationError("header varint too long")


def build_nonce_candidate(template: Template, nonce_hex: str) -> NonceCandidate:
    """Reconstruct both native blobs while changing only the header nonce."""
    if not isinstance(template, Template):
        raise VerificationError("validated native template required")
    if (not isinstance(nonce_hex, str) or len(nonce_hex) != 8 or
            any(c not in "0123456789abcdefABCDEF" for c in nonce_hex)):
        raise VerificationError("nonce must be exactly four hex bytes")
    nonce = bytes.fromhex(nonce_hex)
    full = template.blocktemplate_blob
    hashing = template.blockhashing_blob
    cursor = 0
    for _ in range(3):  # major version, minor version, timestamp
        cursor = _read_varint(hashing, cursor)
    offset = cursor + 32  # previous block hash
    end = offset + 4
    if end > len(full) or end > len(hashing):
        raise VerificationError("incomplete native block header")
    if full[:end] != hashing[:end]:
        raise VerificationError("native header differs between template blobs")
    if full[offset:end] == nonce:
        raise VerificationError("nonce must modify the original template")
    changed_full = full[:offset] + nonce + full[end:]
    changed_hashing = hashing[:offset] + nonce + hashing[end:]
    if changed_full[:end] != changed_hashing[:end]:
        raise VerificationError("candidate header mismatch")
    return NonceCandidate(offset, nonce, changed_full, changed_hashing)
