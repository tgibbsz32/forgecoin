"""Research-only bridge: daemon template -> bound miner job -> full candidate.

Never makes RPC calls, credits shares, pays wallets, or submits blocks.
Strictly limited to disposable height-one/difficulty-one, one-tx templates.
"""
from dataclasses import dataclass, replace
import hmac

from .bound_job import BoundJobVerifier, _varint
from .pow_boundary import VerificationError
from .reserved_candidate import build_reserved_candidate
from .template_adapter import Template


@dataclass(frozen=True)
class VerifiedMinerCandidate:
    full_block_blob: bytes
    hashing_blob: bytes
    nonce_hex: str
    digest_hex: str
    reserve_hex: str


class IsolatedMinerJob:
    def __init__(self, original: Template, reserve_hex: str):
        if not isinstance(original, Template) or original.height != 1 or original.difficulty != 1:
            raise VerificationError("only disposable height-one difficulty-one templates")
        if original.reserve_size != 8:
            raise VerificationError("requires an eight-byte native coinbase reservation")
        if not isinstance(reserve_hex, str) or len(reserve_hex) != 16:
            raise VerificationError("invalid miner reservation")
        offset = 0
        for _ in range(3):
            offset = _varint(original.blockhashing_blob, offset)
        offset += 32
        if offset + 4 > len(original.blockhashing_blob):
            raise VerificationError("incomplete original nonce")
        original_nonce = original.blockhashing_blob[offset:offset + 4].hex()
        # Change the coinbase reservation first. XMRig then varies only the nonce.
        prepared = build_reserved_candidate(
            original, reserve_hex=reserve_hex, nonce_hex=original_nonce)
        self.original = original
        self.reserve_hex = reserve_hex.lower()
        self.prepared = replace(
            original, blocktemplate_blob=prepared.full_block_blob,
            blockhashing_blob=prepared.hashing_blob)
        self.verifier = BoundJobVerifier()
        self.job_id = self.verifier.register(self.prepared, 1)
        self.nonce_offset = prepared.nonce_offset
        if self.nonce_offset != 39:
            raise VerificationError("this isolated XMRig rx/0 test requires nonce offset 39")

    def verify_submission(self, job_id, nonce_hex, digest_hex, native_verifier):
        if job_id != self.job_id or not isinstance(digest_hex, str) or len(digest_hex) != 64:
            raise VerificationError("invalid job or claimed digest")
        result = self.verifier.inspect(job_id, nonce_hex, 1, native_verifier)
        if result.status != "POW_THRESHOLD_MET_UNCREDITED":
            raise VerificationError("share does not meet isolated network difficulty")
        if not hmac.compare_digest(result.digest_hex, digest_hex.lower()):
            raise VerificationError("claimed native RandomX digest differs")
        rebuilt = build_reserved_candidate(
            self.original, reserve_hex=self.reserve_hex, nonce_hex=nonce_hex)
        expected = (
            self.prepared.blockhashing_blob[:self.nonce_offset]
            + bytes.fromhex(nonce_hex)
            + self.prepared.blockhashing_blob[self.nonce_offset + 4:])
        if rebuilt.hashing_blob != expected:
            raise VerificationError("miner submission differs from complete candidate")
        return VerifiedMinerCandidate(
            rebuilt.full_block_blob, rebuilt.hashing_blob,
            nonce_hex.lower(), result.digest_hex, self.reserve_hex)
