"""Offline native consensus reconstruction of a coinbase-reserve variant.

Test/research only. Does not contact a daemon, mine, submit blocks, or credit
shares. Requires a source-matched, explicitly checksummed native helper.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile

from .template_adapter import Template
from .pow_boundary import VerificationError


@dataclass(frozen=True)
class ReserveCandidate:
    full_block_blob: bytes
    hashing_blob: bytes
    reserve_offset: int
    reserve_bytes: bytes


def check_result(template: Template, replacement: bytes, output: str) -> ReserveCandidate:
    if not isinstance(template, Template) or not isinstance(replacement, bytes) or len(replacement) != 8:
        raise VerificationError("validated template and eight reserve bytes required")
    lines = output.splitlines()
    if len(lines) != 3:
        raise VerificationError("unexpected native reconstruction response")
    fields = {}
    for line in lines:
        if " " not in line:
            raise VerificationError("invalid native output")
        key, value = line.split(" ", 1)
        if key in fields or key not in ("FULL", "HASHING", "OFFSET"):
            raise VerificationError("invalid native output field")
        fields[key] = value
    if set(fields) != {"FULL", "HASHING", "OFFSET"}:
        raise VerificationError("incomplete native output")
    full_hex, hash_hex = fields["FULL"], fields["HASHING"]
    for value in (full_hex, hash_hex):
        if len(value) % 2 or len(value) > 524288 or not re.fullmatch("[0-9a-f]+", value):
            raise VerificationError("invalid native hex output")
    if fields["OFFSET"] != str(template.reserved_offset):
        raise VerificationError("reserve offset changed")
    full, hashing = bytes.fromhex(full_hex), bytes.fromhex(hash_hex)
    original = template.blocktemplate_blob
    start = template.reserved_offset
    if (template.reserve_size != 8 or start + 8 > len(original)
            or original[start:start + 8] == replacement
            or len(full) != len(original) or len(hashing) != len(template.blockhashing_blob)
            or full != original[:start] + replacement + original[start + 8:]
            or hashing == template.blockhashing_blob
            or hashing[:39] != template.blockhashing_blob[:39]):
        raise VerificationError("native result differs outside intended reserve/tree root")
    return ReserveCandidate(full, hashing, start, replacement)


def build_reserve_candidate(template: Template, replacement: bytes,
                            executable: Path, expected_sha256: str) -> ReserveCandidate:
    """Invoke the native consensus helper once; no fallback or network access."""
    if not isinstance(template, Template) or template.reserve_size != 8:
        raise VerificationError("eight-byte native template required")
    if not isinstance(replacement, bytes) or len(replacement) != 8:
        raise VerificationError("eight reserve bytes required")
    if not isinstance(expected_sha256, str) or not re.fullmatch("[0-9a-fA-F]{64}", expected_sha256):
        raise VerificationError("pinned native helper digest required")
    path = Path(executable).resolve(strict=True)
    if not path.is_file() or path.name.lower() != "forge-isolated-block-reconstruct.exe":
        raise VerificationError("unexpected native helper executable")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256.lower():
        raise VerificationError("native helper digest mismatch")
    payload = "\n".join((
        template.blocktemplate_blob.hex(),
        template.blockhashing_blob.hex(),
        str(template.reserved_offset),
        replacement.hex())) + "\n"
    with tempfile.TemporaryDirectory(prefix="frg-reserve-offline-") as folder:
        input_file = Path(folder) / "input.txt"
        input_file.write_text(payload, encoding="ascii")
        try:
            result = subprocess.run([str(path), str(input_file)], capture_output=True,
                                    text=True, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise VerificationError("native block reconstruction unavailable") from error
    if result.returncode != 0 or len(result.stdout) > 1048576:
        raise VerificationError("native block reconstruction failed (exit=%d, reason=%s)" % (result.returncode, result.stderr.strip()[-180:]))
    return check_result(template, replacement, result.stdout)
