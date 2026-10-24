"""Offline header decoding and nonce replacement, not RandomX verification.

Layout follows block_header serialization and get_block_hashing_blob in the
native source. The transaction tree root is carried through, not recomputed.
"""
from dataclasses import dataclass


def read_varint(blob, offset, bits=64):
    start = offset
    value = 0
    for shift in range(0, bits, 7):
        if offset >= len(blob):
            raise ValueError("truncated header varint")
        byte = blob[offset]
        offset += 1
        value |= (byte & 127) << shift
        if value >= 1 << bits:
            raise ValueError("header varint overflow")
        if not byte & 128:
            if offset - start > 1 and byte == 0:
                raise ValueError("noncanonical header varint")
            return value, offset
    raise ValueError("unterminated header varint")


@dataclass(frozen=True)
class Header:
    major: int
    minor: int
    timestamp: int
    previous_hash: bytes
    nonce: int
    nonce_offset: int
    end: int


def decode_header(blob):
    major, offset = read_varint(blob, 0, 8)
    minor, offset = read_varint(blob, offset, 8)
    timestamp, offset = read_varint(blob, offset)
    if offset + 36 > len(blob):
        raise ValueError("truncated block header")
    previous = blob[offset:offset + 32]
    offset += 32
    return Header(major, minor, timestamp, previous,
                  int.from_bytes(blob[offset:offset + 4], "little"), offset, offset + 4)


@dataclass(frozen=True)
class MiningWork:
    header: Header
    hashing_blob: bytes
    block_blob: bytes
    transaction_count: int

    def with_nonce(self, nonce):
        """Return matching hashing/block blobs; never change reserve or tree root."""
        if type(nonce) is not int or not 0 <= nonce < 1 << 32:
            raise ValueError("nonce must be uint32")
        start = self.header.nonce_offset
        encoded = nonce.to_bytes(4, "little")
        return tuple(blob[:start] + encoded + blob[start + 4:]
                     for blob in (self.hashing_blob, self.block_blob))


def prepare_work(template):
    header = decode_header(template.blockhashing_blob)
    block_header = decode_header(template.blocktemplate_blob)
    if header != block_header:
        raise ValueError("template and hashing headers differ")
    if template.reserved_offset < header.end:
        raise ValueError("reserved region overlaps block header")
    # Hashing blob = serialized header + 32-byte transaction root + tx count.
    count, end = read_varint(template.blockhashing_blob, header.end + 32)
    if count == 0 or end != len(template.blockhashing_blob):
        raise ValueError("invalid hashing blob transaction count or trailing bytes")
    return MiningWork(header, template.blockhashing_blob,
                      template.blocktemplate_blob, count)
