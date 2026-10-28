#!/usr/bin/env python3
"""Cross-check two user-supplied, OFFLINE Solana SPL mint RPC snapshots.

NEVER calls RPC, signs, spends, mints, or transfers. Matching files cannot
prove that either originated on mainnet, that sources are independent, or
that a user owns the token. A verified mainnet identity requires separate
authenticated evidence and independent human review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

from verify_mfrg_mint_snapshot import SnapshotError, assess_snapshot

MAX_SLOT_GAP = 1500
REQUIRED_EQUAL = (
    "program", "decimals", "raw_supply_atomic", "mint_authority",
    "freeze_authority", "fixed_supply_in_snapshot", "decision"
)


class ReconciliationError(ValueError):
    """Offline evidence is malformed, contradictory, or insufficient."""


def claimed_host(origin):
    """Require explicit https origin; do not record credentials or API keys."""
    if not isinstance(origin, str):
        raise ReconciliationError("Provider origin must be https://hostname")
    try:
        url = urlsplit(origin)
        host = url.hostname
        port = url.port
    except ValueError as exc:
        raise ReconciliationError("Invalid provider origin") from exc
    if (url.scheme != "https" or not host or url.username or url.password
            or url.query or url.fragment or url.path not in ("", "/")
            or port not in (None, 443)
            or host in ("localhost", "127.0.0.1", "::1")
            or "." not in host or any(c.isspace() for c in host)):
        raise ReconciliationError("Require a public HTTPS origin without credentials or paths")
    return host.lower().rstrip(".")


def digest(payload):
    # Hashes support audit trail integrity, not RPC provenance authentication.
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def reconcile(mint_address, first, second, first_origin, second_origin):
    host1, host2 = claimed_host(first_origin), claimed_host(second_origin)
    if host1 == host2:
        raise ReconciliationError("Require two different claimed RPC hostnames")
    try:
        a = assess_snapshot(mint_address, first)
        b = assess_snapshot(mint_address, second)
    except SnapshotError as exc:
        raise ReconciliationError(str(exc)) from exc
    mismatches = [key for key in REQUIRED_EQUAL if a[key] != b[key]]
    if mismatches:
        raise ReconciliationError(
            "RPC snapshots conflict on: " + ", ".join(mismatches)
        )
    gap = abs(a["snapshot_slot"] - b["snapshot_slot"])
    if gap > MAX_SLOT_GAP:
        raise ReconciliationError("Snapshot slot gap too large; collect fresher evidence")
    if first == second:
        # Identical synthetic snapshots can be copied across source labels.
        # Even distinct byte content cannot authenticate provider independence.
        raise ReconciliationError("Identical RPC documents are not independent evidence")
    return {
        "requested_mint": mint_address,
        "claimed_sources": [host1, host2],
        "snapshot_slots": [a["snapshot_slot"], b["snapshot_slot"]],
        "slot_gap": gap,
        "sha256_evidence": [digest(first), digest(second)],
        "matching_program": a["program"],
        "matching_decimals": a["decimals"],
        "matching_raw_supply_atomic": a["raw_supply_atomic"],
        "matching_mint_authority": a["mint_authority"],
        "matching_freeze_authority": a["freeze_authority"],
        "matching_policy_classification": a["decision"],
        "offline_comparison_passed": True,
        "rpc_provenance_authenticated": False,
        "independent_network_sources_proven": False,
        "mint_ownership_proven": False,
        "account_holdings_reconciled": False,
        "treasury_funding_proven": False,
        "founder_vesting_deployed": False,
        "sale_or_issuance_authorized": False,
        "next_gate": (
            "Authenticate both finalized mainnet RPC sources and mint creation "
            "signature externally; verify issuer authority and all holder/token "
            "account inventory before planning any transactions."
        ),
    }


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ReconciliationError("Cannot read valid RPC snapshot: " + str(exc)) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mint", required=True, help="Authentic mainnet mint address, obtained independently")
    parser.add_argument("--first-json", type=Path, required=True, help="Offline getAccountInfo(jsonParsed) result")
    parser.add_argument("--second-json", type=Path, required=True, help="Another offline getAccountInfo(jsonParsed) result")
    parser.add_argument("--first-origin", required=True, help="Claimed first HTTPS RPC origin, no API key")
    parser.add_argument("--second-origin", required=True, help="Claimed second HTTPS RPC origin, no API key")
    args = parser.parse_args(argv)
    try:
        if args.first_json.resolve() == args.second_json.resolve():
            raise ReconciliationError("Evidence files must be different files")
        result = reconcile(
            args.mint, read_json(args.first_json), read_json(args.second_json),
            args.first_origin, args.second_origin,
        )
    except ReconciliationError as exc:
        print(json.dumps({"offline_comparison_passed": False,
                          "rpc_provenance_authenticated": False,
                          "sale_or_issuance_authorized": False,
                          "error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
