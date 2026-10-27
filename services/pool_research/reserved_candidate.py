"""Offline coinbase-reserve block reconstruction for one-transaction test templates.

Only source-matched, empty isolated blocks with a v2 null-RCT coinbase are
supported. Never reuses the original hashing blob after changing the coinbase:
the miner transaction hash (single-leaf tree root) MUST be recalculated.
No network, daemon, wallet, mining or payouts.
"""
from dataclasses import dataclass

from .nonce_candidate import _read_varint
from .pow_boundary import VerificationError
from .template_adapter import Template

_MASK = (1 << 64) - 1
_ROUNDS = (
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
)
_ROTATIONS = (
    0, 1, 62, 28, 27, 36, 44, 6, 55, 20, 3, 10, 43,
    25, 39, 41, 45, 15, 21, 8, 18, 2, 61, 56, 14,
)


def _rotate(value, count):
    return ((value << count) | (value >> (64 - count))) & _MASK if count else value


def _keccak_f(state):
    for constant in _ROUNDS:
        c = [state[x] ^ state[x+5] ^ state[x+10] ^ state[x+15] ^ state[x+20] for x in range(5)]
        for x in range(5):
            delta = c[(x-1) % 5] ^ _rotate(c[(x+1) % 5], 1)
            for y in range(5):
                state[x+5*y] ^= delta
        b = [0]*25
        for x in range(5):
            for y in range(5):
                b[y+5*((2*x+3*y)%5)] = _rotate(state[x+5*y], _ROTATIONS[x+5*y])
        for x in range(5):
            for y in range(5):
                state[x+5*y] = b[x+5*y] ^ ((~b[(x+1)%5+5*y]) & b[(x+2)%5+5*y])
        state[0] ^= constant


def keccak_256(data: bytes) -> bytes:
    """Legacy Keccak-256 (CryptoNote cn_fast_hash), NOT NIST SHA3-256."""
    if not isinstance(data, bytes):
        raise TypeError("hash input must be bytes")
    rate = 136
    padded = bytearray(data)
    padded.append(0x01)
    padded.extend(bytes((-len(padded)-1) % rate))
    padded.append(0x80)
    state = [0]*25
    for offset in range(0, len(padded), rate):
        block = padded[offset:offset+rate]
        for index in range(rate//8):
            state[index] ^= int.from_bytes(block[index*8:index*8+8], "little")
        _keccak_f(state)
    return b"".join(word.to_bytes(8, "little") for word in state)[:32]


def _varint(data, offset):
    start = offset
    end = _read_varint(data, start)
    # Decoder in nonce_candidate returns next offset only.
    value = 0
    for index, byte in enumerate(data[start:end]):
        value |= (byte & 127) << (7*index)
    return value, end


def _coinbase_prefix_end(blob, offset):
    tx_start = offset
    version, offset = _varint(blob, offset)
    if version != 2:
        raise VerificationError("only null-RCT v2 miner transactions supported")
    _, offset = _varint(blob, offset)  # unlock time
    inputs, offset = _varint(blob, offset)
    if inputs != 1 or offset >= len(blob) or blob[offset] != 0xff:
        raise VerificationError("not a single-generation miner transaction")
    offset += 1
    _, offset = _varint(blob, offset)  # coinbase height
    count, offset = _varint(blob, offset)
    if not 1 <= count <= 16:
        raise VerificationError("unsupported coinbase output count")
    for _ in range(count):
        _, offset = _varint(blob, offset)
        if offset >= len(blob):
            raise VerificationError("truncated coinbase output type")
        target = blob[offset]
        offset += 1
        if target not in (2, 3):
            raise VerificationError("unsupported coinbase output")
        offset += 32 if target == 2 else 33
        if offset > len(blob):
            raise VerificationError("truncated output key")
    extra_len, offset = _varint(blob, offset)
    extra_start = offset
    offset += extra_len
    if offset+2 != len(blob) or blob[offset:] != b"\x00\x00":
        raise VerificationError("expected null-RCT coinbase and zero other transactions")
    return tx_start, extra_start, offset


def _miner_tx_root(blob, tx_start, prefix_end):
    prefix_hash = keccak_256(bytes(blob[tx_start:prefix_end]))
    base_hash = keccak_256(b"\x00")
    return keccak_256(prefix_hash + base_hash + bytes(32))


@dataclass(frozen=True)
class ReservedCandidate:
    full_block_blob: bytes
    hashing_blob: bytes
    nonce_offset: int
    reserved_offset: int
    tree_root: bytes


def build_reserved_candidate(template: Template, *, reserve_hex: str, nonce_hex: str) -> ReservedCandidate:
    if not isinstance(template, Template):
        raise VerificationError("validated template required")
    if template.height != 1 or template.difficulty != 1:
        raise VerificationError("requires disposable height 1, difficulty 1")
    if (not isinstance(reserve_hex, str) or len(reserve_hex) != template.reserve_size*2
            or any(c not in "0123456789abcdefABCDEF" for c in reserve_hex)):
        raise VerificationError("reserved bytes must match requested reservation length")
    if (not isinstance(nonce_hex, str) or len(nonce_hex) != 8
            or any(c not in "0123456789abcdefABCDEF" for c in nonce_hex)):
        raise VerificationError("nonce must be exactly four hex bytes")
    full, hashing = template.blocktemplate_blob, template.blockhashing_blob
    offset = 0
    for _ in range(3):
        offset = _read_varint(full, offset)
    nonce_offset = offset+32
    header_end = nonce_offset+4
    if (len(hashing) != header_end+33 or full[:header_end] != hashing[:header_end]
            or hashing[-1:] != b"\x01"):
        raise VerificationError("not a matching one-transaction native header")
    tx_start, extra_start, prefix_end = _coinbase_prefix_end(full, header_end)
    if (template.reserved_offset < extra_start+2 or
            template.reserved_offset+template.reserve_size != prefix_end or
            template.reserve_size > 255 or
            full[template.reserved_offset-2:template.reserved_offset]
            != bytes((2, template.reserve_size))):
        raise VerificationError("reserved region is not the final coinbase extra-nonce field")
    original_root = _miner_tx_root(full, tx_start, prefix_end)
    if original_root != hashing[header_end:header_end+32]:
        raise VerificationError("native template hashing blob has inconsistent transaction root")
    reserve = bytes.fromhex(reserve_hex)
    nonce = bytes.fromhex(nonce_hex)
    if reserve == full[template.reserved_offset:template.reserved_offset+template.reserve_size]:
        raise VerificationError("reserved bytes must actually change")
    changed = bytearray(full)
    changed[template.reserved_offset:template.reserved_offset+template.reserve_size] = reserve
    changed[nonce_offset:header_end] = nonce
    new_root = _miner_tx_root(changed, tx_start, prefix_end)
    if new_root == original_root:
        raise VerificationError("coinbase edit did not alter transaction root")
    return ReservedCandidate(
        full_block_blob=bytes(changed),
        hashing_blob=bytes(changed[:header_end])+new_root+b"\x01",
        nonce_offset=nonce_offset,
        reserved_offset=template.reserved_offset,
        tree_root=new_root,
    )
