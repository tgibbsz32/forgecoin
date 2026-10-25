"""Isolated ForgeCoin daemon-template to RandomX miner-job boundary.

This is a *read-only*, loopback-only and uncredited research integration.
It NEVER submits a block, credits a reward, signs a payout or opens Stratum.
Caller supplies an approved disposable wallet address, a pinned genesis hash
and an explicitly trusted native RandomX(seed, hashing_blob) verifier.

Worker-specific extra_nonce bytes come from the OS CSPRNG; they are incorporated
by the daemon into the coinbase, hashing blob and block template, NOT patched
locally. A changing chain tip invalidates jobs before and after verification.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
import secrets
import time
from typing import Callable
from urllib.parse import urlsplit
from urllib.request import Request, ProxyHandler, HTTPRedirectHandler, build_opener

from .bound_job import BoundJobVerifier
from .pow_boundary import VerificationError, VerificationResult
from .template_adapter import TemplateError, validate_template

_HEX_32 = re.compile(r"\A[0-9a-fA-F]{64}\Z")
_HEX_DIGEST = re.compile(r"\A[0-9a-fA-F]{64}\Z")
_NONCE = re.compile(r"\A[0-9a-fA-F]{8}\Z")
_METHODS = frozenset(("get_info", "get_block_header_by_height", "get_block_template"))


class DaemonJobError(ValueError):
    pass


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LoopbackDaemonRpc:
    """Bounded JSON-RPC to an explicitly designated numeric-loopback daemon.

    No proxy, redirect, URL-controlled RPC method, public RPC or wallet RPC.
    Constructing this client performs no network requests.
    """
    def __init__(self, endpoint: str, timeout: float = 5):
        try:
            parts = urlsplit(endpoint)
            port = parts.port
        except ValueError as exc:
            raise DaemonJobError("invalid daemon RPC endpoint") from exc
        if (parts.scheme != "http" or parts.hostname not in ("127.0.0.1", "::1")
                or parts.path not in ("", "/json_rpc") or parts.username
                or parts.password or parts.query or parts.fragment
                or port is None or not 1 <= port <= 65535):
            raise DaemonJobError("explicit numeric-loopback HTTP /json_rpc required")
        if type(timeout) not in (int, float) or not 0 < timeout <= 10:
            raise DaemonJobError("invalid daemon RPC timeout")
        self.endpoint = endpoint.rstrip("/") if parts.path else endpoint.rstrip("/") + "/json_rpc"
        self.timeout = timeout
        self._opener = build_opener(ProxyHandler({}), _NoRedirects())

    def __call__(self, method: str, params: dict | None = None) -> dict:
        if method not in _METHODS or (params is not None and not isinstance(params, dict)):
            raise DaemonJobError("RPC method is not allowed")
        payload = json.dumps({
            "jsonrpc": "2.0", "id": "frg-job-readonly",
            "method": method, "params": params or {},
        }, separators=(",", ":")).encode("ascii")
        request = Request(self.endpoint, payload, {"Content-Type": "application/json"}, method="POST")
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise DaemonJobError("daemon RPC HTTP failure")
                raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise DaemonJobError("daemon RPC response exceeds limit")
            data = json.loads(raw)
        except (OSError, ValueError, UnicodeError) as exc:
            if isinstance(exc, DaemonJobError):
                raise
            raise DaemonJobError("daemon RPC unavailable or malformed") from exc
        if (not isinstance(data, dict) or data.get("id") != "frg-job-readonly"
                or data.get("error") is not None or not isinstance(data.get("result"), dict)):
            raise DaemonJobError("invalid daemon JSON-RPC envelope")
        return data["result"]


@dataclass(frozen=True)
class WorkerJob:
    worker: str
    job_id: str
    height: int
    prev_hash: str
    seed_hash: str
    hashing_blob_hex: str
    worker_difficulty: int
    network_difficulty: int
    expires_at: float

    def xmrig_job(self) -> dict:
        """Stratum-shaped job data; NOT evidence of a production Stratum server."""
        target = (0xFFFFFFFF // self.worker_difficulty).to_bytes(4, "little").hex()
        return {
            "job_id": self.job_id,
            "height": self.height,
            "blob": self.hashing_blob_hex,
            "seed_hash": self.seed_hash,
            "algo": "rx/0",
            "target": target,
        }


class DaemonJobSource:
    """Single-process isolated worker job issuer, fail-closed on chain changes.

    Thread-safety, job persistence and full Stratum lifecycle are NOT provided.
    The caller must serialize invocations. MAX outstanding jobs is bounded.
    """
    def __init__(self, rpc: Callable, *, expected_genesis_hash: str,
                 expected_nettype: str, wallet_address: str,
                 max_jobs: int = 16, job_ttl: int = 60, clock: Callable = time.monotonic):
        if not callable(rpc):
            raise DaemonJobError("explicit daemon RPC callback required")
        if not isinstance(expected_genesis_hash, str) or not _HEX_32.fullmatch(expected_genesis_hash):
            raise DaemonJobError("verified network genesis hash is mandatory")
        if expected_nettype not in ("mainnet", "testnet", "stagenet"):
            raise DaemonJobError("explicit network type required")
        if not isinstance(wallet_address, str) or not 10 <= len(wallet_address) <= 256:
            raise DaemonJobError("explicit disposable mining address required")
        if type(max_jobs) is not int or not 1 <= max_jobs <= 32:
            raise DaemonJobError("invalid job capacity")
        if type(job_ttl) is not int or not 1 <= job_ttl <= 120:
            raise DaemonJobError("invalid job lifetime")
        self.rpc, self.genesis = rpc, expected_genesis_hash.lower()
        self.nettype, self.address = expected_nettype, wallet_address
        self.max_jobs, self.ttl, self.clock = max_jobs, job_ttl, clock
        self._bound = BoundJobVerifier()
        self._jobs: dict[str, WorkerJob] = {}

    def _tip(self) -> tuple[int, str]:
        data = self.rpc("get_info")
        if not isinstance(data, dict):
            raise DaemonJobError("invalid daemon chain information")
        height, hash_hex = data.get("height"), data.get("top_block_hash")
        if (type(height) is not int or height < 1
                or not isinstance(hash_hex, str) or not _HEX_32.fullmatch(hash_hex)
                or data.get("nettype") != self.nettype
                or data.get("synchronized") is not True
                or data.get("busy_syncing") is True
                or data.get("untrusted") is True):
            raise DaemonJobError("daemon is unsynchronized, wrong network or invalid tip")
        return height, hash_hex.lower()

    def _genesis_check(self) -> None:
        result = self.rpc("get_block_header_by_height", {"height": 0})
        if not isinstance(result, dict) or not isinstance(result.get("block_header"), dict):
            raise DaemonJobError("daemon genesis header unavailable")
        h = result["block_header"]
        if (h.get("height") != 0 or not isinstance(h.get("hash"), str)
                or h["hash"].lower() != self.genesis):
            raise DaemonJobError("daemon genesis does not match pinned network identity")

    def issue(self, worker: str, worker_difficulty: int) -> WorkerJob:
        if not isinstance(worker, str) or not 1 <= len(worker) <= 64 or not worker.isascii():
            raise DaemonJobError("invalid worker label")
        if type(worker_difficulty) is not int or not 1 <= worker_difficulty <= 0xFFFFFFFF:
            raise DaemonJobError("invalid worker difficulty")
        if len(self._jobs) >= self.max_jobs or worker in self._jobs:
            raise DaemonJobError("worker already has job or issuer is full")
        self._genesis_check()
        tip_before = self._tip()
        extra = secrets.token_bytes(8)
        raw = self.rpc("get_block_template", {
            "wallet_address": self.address, "extra_nonce": extra.hex(),
        })
        if not isinstance(raw, dict) or raw.get("status") != "OK":
            raise DaemonJobError("daemon did not return a successful template")
        try:
            template = validate_template(raw, reserve_size=len(extra))
        except TemplateError as exc:
            raise DaemonJobError("malformed daemon block template") from exc
        if (template.height != tip_before[0] or not isinstance(raw.get("prev_hash"), str)
                or raw["prev_hash"].lower() != tip_before[1]
                or template.difficulty < 1
                or template.blocktemplate_blob[
                    template.reserved_offset:template.reserved_offset + 8] != extra):
            raise DaemonJobError("template is not bound to requested worker or chain tip")
        # Ensure the hashing blob corresponds to the same serialized header.
        blob = template.blockhashing_blob
        cursor = 0
        from .bound_job import _varint
        try:
            for _ in range(3):
                cursor = _varint(blob, cursor)
        except VerificationError as exc:
            raise DaemonJobError("invalid block hashing header") from exc
        if (cursor + 36 > len(blob) or cursor + 36 > len(template.blocktemplate_blob)
                or blob[:cursor + 36] != template.blocktemplate_blob[:cursor + 36]
                or blob[cursor:cursor + 32] != bytes.fromhex(tip_before[1])):
            raise DaemonJobError("hashing blob/header mismatch")
        if self._tip() != tip_before:
            raise DaemonJobError("network tip changed during template issuance")
        try:
            job_id = self._bound.register(template, worker_difficulty)
        except (VerificationError, ValueError) as exc:
            raise DaemonJobError("bound template registration failed") from exc
        job = WorkerJob(
            worker, job_id, template.height, tip_before[1], template.seed_hash.hex(),
            blob.hex(), worker_difficulty, template.difficulty, self.clock() + self.ttl
        )
        self._jobs[worker] = job
        return job

    def inspect(self, worker: str, job_id: str, nonce_hex: str,
                claimed_digest_hex: str, verifier: Callable) -> VerificationResult:
        job = self._jobs.get(worker) if isinstance(worker, str) else None
        if not job or job.job_id != job_id:
            raise DaemonJobError("job not assigned to this worker")
        if not isinstance(claimed_digest_hex, str) or not _HEX_DIGEST.fullmatch(claimed_digest_hex):
            raise DaemonJobError("malformed claimed digest")
        if not isinstance(nonce_hex, str) or not _NONCE.fullmatch(nonce_hex):
            raise DaemonJobError("malformed nonce")
        if self.clock() >= job.expires_at or self._tip() != (job.height, job.prev_hash):
            raise DaemonJobError("worker job expired or chain tip changed")
        try:
            result = self._bound.inspect(job_id, nonce_hex, job.height, verifier)
        except (VerificationError, ValueError) as exc:
            raise DaemonJobError("native share verification failed") from exc
        if result.digest_hex is None:
            # A low-difficulty check has no verified digest in the result.
            raise DaemonJobError("low-difficulty share; no credit")
        import hmac
        if not hmac.compare_digest(result.digest_hex, claimed_digest_hex.lower()):
            raise DaemonJobError("miner-supplied digest disagrees with native RandomX")
        if self.clock() >= job.expires_at or self._tip() != (job.height, job.prev_hash):
            raise DaemonJobError("job became stale during native verification")
        # Research-only. Never call submit_block or payout code from here.
        return VerificationResult("POW_THRESHOLD_MET_UNCREDITED", result.digest_hex)
