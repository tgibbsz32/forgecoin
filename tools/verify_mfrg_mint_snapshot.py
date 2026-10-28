#!/usr/bin/env python3
"""Read-only, OFFLINE parser for a supplied Solana mainnet mint RPC snapshot.

Does not contact RPC, authenticate the snapshot, sign, mint, transfer, or change
authorities. A valid result means the JSON is self-consistent, NOT that a real
mainnet mint or the user's beneficial ownership has been independently verified.
"""
import argparse
import json
import sys
from pathlib import Path

TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
DEVNET_TEST_MINT = "9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw"
BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
TARGET_TOKENS = 500_000_000
DECIMALS = 6
TARGET_ATOMIC = TARGET_TOKENS * 10 ** DECIMALS


class SnapshotError(ValueError):
    pass


def validate_pubkey(value):
    if not isinstance(value, str) or not 32 <= len(value) <= 44:
        raise SnapshotError("Mint must be an exact Solana base58 public key")
    if any(ch not in BASE58 for ch in value):
        raise SnapshotError("Mint has invalid base58 characters")
    n = 0
    for ch in value:
        n = n * 58 + BASE58.index(ch)
    zeros = len(value) - len(value.lstrip("1"))
    b = b"\x00" * zeros + n.to_bytes((n.bit_length() + 7) // 8, "big")
    if len(b) != 32:
        raise SnapshotError("Mint must decode to exactly 32 bytes")
    return value


def assess_snapshot(mint_address, snapshot):
    """Analyze getAccountInfo(... encoding=jsonParsed) response, no network use."""
    validate_pubkey(mint_address)
    if mint_address == DEVNET_TEST_MINT:
        raise SnapshotError("Historical devnet mFRG mint is not the mainnet mint")
    if not isinstance(snapshot, dict) or snapshot.get("id") != mint_address:
        raise SnapshotError("Snapshot RPC id must equal the requested mint address")
    response = snapshot.get("result")
    if not isinstance(response, dict):
        raise SnapshotError("No successful getAccountInfo result")
    ctx = response.get("context")
    if not isinstance(ctx, dict) or type(ctx.get("slot")) is not int or ctx["slot"] <= 0:
        raise SnapshotError("Missing positive Solana observation slot")
    account = response.get("value")
    if not isinstance(account, dict):
        raise SnapshotError("Mint account absent; no issuance can be inferred")
    if account.get("owner") != TOKEN_PROGRAM:
        raise SnapshotError("Account not owned by standard SPL Token Program")
    if account.get("executable") is not False:
        raise SnapshotError("Mint account cannot be executable")
    data = account.get("data")
    if (not isinstance(data, dict) or data.get("program") != "spl-token"
            or not isinstance(data.get("parsed"), dict)
            or data["parsed"].get("type") != "mint"):
        raise SnapshotError("Expected a jsonParsed standard SPL mint account")
    info = data["parsed"].get("info")
    if not isinstance(info, dict):
        raise SnapshotError("Missing decoded mint metadata")
    required = {"isInitialized", "decimals", "supply", "mintAuthority", "freezeAuthority"}
    if not required.issubset(info):
        raise SnapshotError("Incomplete mint data: absence of an authority field is NOT revocation")
    if info.get("isInitialized") is not True:
        raise SnapshotError("SPL mint is not initialized")
    if type(info.get("decimals")) is not int or info["decimals"] != DECIMALS:
        raise SnapshotError("Expected mFRG six-decimal standard SPL mint")
    supply = info.get("supply")
    if (not isinstance(supply, str) or not supply.isascii()
            or not supply.isdecimal() or len(supply) > 20):
        raise SnapshotError("Expected exact nonnegative raw integer supply string")
    raw = int(supply)
    if raw > 2 ** 64 - 1:
        raise SnapshotError("Raw supply exceeds SPL u64")
    if raw > TARGET_ATOMIC:
        raise SnapshotError("Observed supply exceeds 500M mFRG policy maximum")
    mint_authority = info.get("mintAuthority")
    freeze_authority = info.get("freezeAuthority")
    for name, authority in (("mintAuthority", mint_authority),
                            ("freezeAuthority", freeze_authority)):
        if authority is not None:
            try:
                validate_pubkey(authority)
            except SnapshotError as exc:
                raise SnapshotError(name + " invalid: " + str(exc)) from exc
    fixed_supply = mint_authority is None
    at_target = raw == TARGET_ATOMIC
    if fixed_supply and at_target:
        decision = "SNAPSHOT_SUGGESTS_FIXED_SUPPLY_AT_TARGET"
    elif fixed_supply:
        decision = "SNAPSHOT_SUGGESTS_IRREVOCABLE_SUPPLY_BELOW_TARGET"
    elif at_target:
        decision = "AT_TARGET_BUT_MINT_AUTHORITY_STILL_ACTIVE"
    else:
        decision = "BELOW_TARGET_AND_MINT_AUTHORITY_ACTIVE"
    return {
        "network_claim": "mainnet-beta (supplied by operator; NOT authenticated)",
        "mint_requested": mint_address,
        "snapshot_slot": ctx["slot"],
        "program": TOKEN_PROGRAM,
        "decimals": DECIMALS,
        "raw_supply_atomic": str(raw),
        "supply_mfrg": f"{raw // 1_000_000}.{raw % 1_000_000:06d}",
        "mint_authority": mint_authority,
        "freeze_authority": freeze_authority,
        "supply_reissuance_possible_under_observed_authority": not fixed_supply,
        "fixed_supply_in_snapshot": fixed_supply,
        "decision": decision,
        "snapshot_self_consistent": True,
        "independently_authenticated_mainnet": False,
        "issuer_or_founder_ownership_proven": False,
        "sale_or_issuance_authorized": False,
        "next_gate": "Authenticate mainnet RPC/source, mint identity and signing authorities independently; reconcile holders and all nine vaults before any issuance or transfer.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mint", required=True, help="Exact 32-byte base58 mainnet SPL mint address")
    parser.add_argument("--rpc-json", required=True, type=Path,
                        help="Saved read-only getAccountInfo jsonParsed response; no network requests")
    args = parser.parse_args(argv)
    try:
        snap = json.loads(args.rpc_json.read_text(encoding="utf-8-sig"))
        report = assess_snapshot(args.mint, snap)
    except (OSError, json.JSONDecodeError, SnapshotError) as exc:
        print(json.dumps({"snapshot_self_consistent": False,
                          "independently_authenticated_mainnet": False,
                          "sale_or_issuance_authorized": False,
                          "error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
