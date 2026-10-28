#!/usr/bin/env python3
"""Offline cross-check of SPL mint initialization and later mint account data.

This tool NEVER authenticates RPC provenance, creates a mint, verifies a
transaction's cryptographic signature from wire bytes, signs, sends or moves
tokens. It only checks internal coherence of untrusted saved jsonParsed
getTransaction responses and an equally untrusted getAccountInfo mint snapshot.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from verify_mfrg_mint_snapshot import (
    TOKEN_PROGRAM, SnapshotError, assess_snapshot, validate_pubkey,
)
from reconcile_mfrg_mint_snapshots import (
    claimed_host, ReconciliationError,
)

MAX_TX_INSTRUCTIONS = 3000
INIT_TYPES = frozenset(("initializeMint", "initializeMint2"))


class InitializationError(ValueError):
    """Incomplete, conflicting or unsafe mint initialization evidence."""


def public_key(value, label):
    try:
        validate_pubkey(value)
    except SnapshotError as exc:
        raise InitializationError(f"{label}: {exc}") from exc
    return value


def signature_key(value):
    """Decode a Solana base58 signature to exactly 64 bytes (no crypto verification)."""
    if not isinstance(value, str) or not 64 <= len(value) <= 88:
        raise InitializationError("Missing or invalid transaction signature")
    digits = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    number = 0
    for char in value:
        index = digits.find(char)
        if index < 0:
            raise InitializationError("Transaction signature has invalid base58")
        number = number * 58 + index
    pad = len(value) - len(value.lstrip("1"))
    decoded = b"\x00" * pad + number.to_bytes((number.bit_length() + 7)//8, "big")
    if len(decoded) != 64:
        raise InitializationError("Transaction signature must decode to exactly 64 bytes")
    return value


def parse_initialization(mint, signature, response):
    """Parse a user-provided getTransaction(encoding=jsonParsed) response."""
    public_key(mint, "mint")
    signature_key(signature)
    if not isinstance(response, dict) or response.get("id") != signature:
        raise InitializationError("getTransaction RPC request id must equal signature")
    transaction_record = response.get("result")
    if not isinstance(transaction_record, dict):
        raise InitializationError("No transaction record: missing or unknown is not absence of a mint")
    slot = transaction_record.get("slot")
    if type(slot) is not int or slot <= 0:
        raise InitializationError("Missing positive transaction slot")
    metadata = transaction_record.get("meta")
    if not isinstance(metadata, dict) or "err" not in metadata or metadata["err"] is not None:
        raise InitializationError("Mint initialization transaction must have successful meta.err=null")
    tx = transaction_record.get("transaction")
    if not isinstance(tx, dict):
        raise InitializationError("Require full jsonParsed transaction result")
    signatures = tx.get("signatures")
    if not isinstance(signatures, list) or not signatures or signatures[0] != signature:
        raise InitializationError("Primary transaction signature does not match request")
    for sig in signatures:
        signature_key(sig)
    message = tx.get("message")
    if not isinstance(message, dict):
        raise InitializationError("Missing parsed transaction message")
    keys = message.get("accountKeys")
    if not isinstance(keys, list) or not keys:
        raise InitializationError("Missing parsed accountKeys")
    seen = set()
    mint_key_writable = False
    for entry in keys:
        if not isinstance(entry, dict):
            raise InitializationError("Expected jsonParsed account key objects")
        key = public_key(entry.get("pubkey"), "transaction account key")
        if key in seen:
            raise InitializationError("Repeated transaction account key")
        seen.add(key)
        if type(entry.get("signer")) is not bool or type(entry.get("writable")) is not bool:
            raise InitializationError("Parsed account key missing signer/writable flags")
        if key == mint and entry["writable"]:
            mint_key_writable = True
    if not mint_key_writable:
        raise InitializationError("Mint must be a writable key in initializing transaction")
    instructions = message.get("instructions")
    if not isinstance(instructions, list):
        raise InitializationError("Missing parsed outer instructions")
    inner = metadata.get("innerInstructions")
    if inner is None:
        inner = []
    if not isinstance(inner, list):
        raise InitializationError("Malformed inner instructions")
    flattened = list(instructions)
    for group in inner:
        if not isinstance(group, dict) or not isinstance(group.get("instructions"), list):
            raise InitializationError("Malformed CPI instruction record")
        flattened.extend(group["instructions"])
    if len(flattened) > MAX_TX_INSTRUCTIONS:
        raise InitializationError("Excessively large instruction list")
    candidates = []
    for instruction in flattened:
        if not isinstance(instruction, dict):
            raise InitializationError("Invalid parsed instruction")
        parsed = instruction.get("parsed")
        if not isinstance(parsed, dict) or parsed.get("type") not in INIT_TYPES:
            continue
        if instruction.get("programId") != TOKEN_PROGRAM:
            continue
        info = parsed.get("info")
        if not isinstance(info, dict) or info.get("mint") != mint:
            continue
        decimals = info.get("decimals")
        if type(decimals) is not int or decimals != 6:
            raise InitializationError("Initializing SPL instruction has wrong decimals")
        mint_authority = public_key(info.get("mintAuthority"), "initial mint authority")
        freeze_authority = info.get("freezeAuthority")
        if freeze_authority is not None:
            public_key(freeze_authority, "initial freeze authority")
        candidates.append({
            "instruction_type": parsed["type"],
            "mint": mint,
            "decimals": decimals,
            "original_mint_authority": mint_authority,
            "original_freeze_authority": freeze_authority,
        })
    if len(candidates) != 1:
        raise InitializationError(
            "Exactly one parsed initializeMint/initializeMint2 instruction for requested SPL mint is required"
        )
    return {"slot": slot, "initialization": candidates[0]}


def report(mint, signature, first, second, snapshot, first_origin, second_origin):
    try:
        hosts = (claimed_host(first_origin), claimed_host(second_origin))
        if hosts[0] == hosts[1]:
            raise InitializationError("Two distinct claimed mainnet RPC hosts required")
        current = assess_snapshot(mint, snapshot)
    except (SnapshotError, ReconciliationError) as exc:
        raise InitializationError(str(exc)) from exc
    a = parse_initialization(mint, signature, first)
    b = parse_initialization(mint, signature, second)
    if a != b:
        raise InitializationError("Claimed initialization transactions disagree on slot or instruction fields")
    if a["slot"] > current["snapshot_slot"]:
        raise InitializationError("Mint account snapshot is from before claimed initialization")
    return {
        "mint": mint,
        "claimed_creation_or_initialization_signature": signature,
        "observed_initialization_slot": a["slot"],
        "later_mint_snapshot_slot": current["snapshot_slot"],
        "claimed_source_hostnames": list(hosts),
        "parsed_initialize_instruction": a["initialization"],
        "later_mint_program": current["program"],
        "later_mint_decimals": current["decimals"],
        "later_raw_supply_atomic": current["raw_supply_atomic"],
        "later_mint_authority": current["mint_authority"],
        "later_freeze_authority": current["freeze_authority"],
        "offline_parsed_evidence_consistent": True,
        "initialized_mint_on_mainnet_authenticated": False,
        "independent_rpc_provenance_verified": False,
        "transaction_signature_cryptographically_verified": False,
        "project_issuer_identity_verified": False,
        "mint_and_holder_custody_verified": False,
        "founder_or_treasury_tokens_funded": False,
        "sale_or_issuance_authorized": False,
        "next_gate": "Authenticate Solana mainnet RPC provenance and real transaction signature externally; verify current mint owner authority and token account inventory before any custody action.",
    }


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise InitializationError(f"Cannot read saved JSON {path}: {exc}") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mint", required=True)
    parser.add_argument("--signature", required=True)
    parser.add_argument("--first-transaction", required=True, type=Path)
    parser.add_argument("--second-transaction", required=True, type=Path)
    parser.add_argument("--mint-json", required=True, type=Path)
    parser.add_argument("--first-origin", required=True)
    parser.add_argument("--second-origin", required=True)
    args = parser.parse_args(argv)
    try:
        evidence = report(
            args.mint, args.signature,
            read_json(args.first_transaction), read_json(args.second_transaction),
            read_json(args.mint_json), args.first_origin, args.second_origin
        )
    except InitializationError as exc:
        print(json.dumps({
            "offline_parsed_evidence_consistent": False,
            "sale_or_issuance_authorized": False,
            "error": str(exc),
        }, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
