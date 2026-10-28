#!/usr/bin/env python3
"""Offline Solana SPL token-account inventory cross-check for miniFORGE.

No network calls, keys, authorization, transactions or writes. Files are
untrusted user-supplied JSON; success proves only internal consistency of
two saved responses, NOT completeness, provenance or beneficial ownership.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from verify_mfrg_mint_snapshot import (
    TOKEN_PROGRAM, DECIMALS, TARGET_ATOMIC, SnapshotError,
    assess_snapshot, validate_pubkey,
)
from reconcile_mfrg_mint_snapshots import claimed_host, ReconciliationError

MAX_SLOT_GAP = 1500
MAX_ACCOUNTS = 100000
UINT64_MAX = 2**64 - 1


class InventoryError(ValueError):
    """Malformed, contradictory or incomplete offline token-account evidence."""


def _raw_amount(v, label):
    if (not isinstance(v, str) or not v or len(v) > 20 or not v.isascii()
            or not v.isdecimal()):
        raise InventoryError(label + ": require exact unsigned integer string")
    number = int(v)
    if number > UINT64_MAX:
        raise InventoryError(label + ": SPL u64 overflow")
    return number


def _key(v, label):
    try:
        return validate_pubkey(v)
    except SnapshotError as exc:
        raise InventoryError(label + ": " + str(exc)) from exc


def parse_inventory(mint, response):
    """Parse a getProgramAccounts(withContext=true, jsonParsed) response.

    The response does not contain the original RPC request/filter arguments.
    Matching balances cannot prove the RPC provider returned all accounts.
    """
    _key(mint, "mint")
    if not isinstance(response, dict) or response.get("id") != mint + ":inventory":
        raise InventoryError("Inventory RPC id must match mint + ':inventory'")
    result = response.get("result")
    if not isinstance(result, dict):
        raise InventoryError("Require withContext result object")
    ctx = result.get("context")
    if (not isinstance(ctx, dict) or type(ctx.get("slot")) is not int
            or ctx["slot"] <= 0):
        raise InventoryError("Missing positive inventory slot")
    entries = result.get("value")
    if not isinstance(entries, list) or len(entries) > MAX_ACCOUNTS:
        raise InventoryError("Missing accounts array or oversized response")

    accounts = {}
    total = 0
    for item in entries:
        if not isinstance(item, dict):
            raise InventoryError("Expected public token-account record")
        address = _key(item.get("pubkey"), "token account")
        if address in accounts:
            raise InventoryError("Duplicate token account " + address)
        account = item.get("account")
        if (not isinstance(account, dict) or account.get("owner") != TOKEN_PROGRAM
                or account.get("executable") is not False):
            raise InventoryError("Invalid SPL token-account program owner")
        data = account.get("data")
        if (not isinstance(data, dict) or data.get("program") != "spl-token"
                or not isinstance(data.get("parsed"), dict)
                or data["parsed"].get("type") != "account"):
            raise InventoryError("Expected jsonParsed SPL account type")
        info = data["parsed"].get("info")
        if not isinstance(info, dict) or info.get("mint") != mint:
            raise InventoryError("Cross-mint account or missing mint field")
        owner = _key(info.get("owner"), "token owner authority")
        amount = info.get("tokenAmount")
        if (not isinstance(amount, dict) or type(amount.get("decimals")) is not int
                or amount["decimals"] != DECIMALS):
            raise InventoryError("Token account decimals differ from mFRG policy")
        raw = _raw_amount(amount.get("amount"), "token amount")
        if info.get("state") not in ("initialized", "frozen"):
            raise InventoryError("Unknown or uninitialized token-account state")
        if "delegate" not in info:
            raise InventoryError("Missing delegate field; absence is not proof of no delegation")
        delegate = info["delegate"]
        if delegate is not None:
            _key(delegate, "delegate authority")
            delegated = info.get("delegatedAmount")
            if not isinstance(delegated, dict):
                raise InventoryError("Delegate present but delegatedAmount absent")
            delegated_raw = _raw_amount(delegated.get("amount"), "delegatedAmount")
            if delegated_raw > raw:
                raise InventoryError("Delegated amount exceeds account amount")
        else:
            delegated_raw = 0
            if "delegatedAmount" in info and isinstance(info["delegatedAmount"], dict):
                if _raw_amount(info["delegatedAmount"].get("amount"), "delegatedAmount") != 0:
                    raise InventoryError("Nonzero delegated amount with no delegate")
        if "closeAuthority" not in info:
            raise InventoryError("Missing closeAuthority; no proof of control")
        close_authority = info["closeAuthority"]
        if close_authority is not None:
            _key(close_authority, "close authority")
        if "isNative" in info and info["isNative"] not in (False, None):
            raise InventoryError("Unexpected wrapped-native token account")
        total += raw
        if total > UINT64_MAX or total > TARGET_ATOMIC:
            raise InventoryError("Total of accounts exceeds supply policy cap")
        accounts[address] = {
            "owner": owner, "raw": raw, "delegate": delegate,
            "delegated": delegated_raw, "state": info["state"],
            "close_authority": close_authority,
        }
    return {"slot": ctx["slot"], "accounts": accounts, "sum_atomic": total}


def reconcile_inventory(mint, mint_snapshot, first, second, origin_first, origin_second):
    """Compare two account scans and one separately saved mint account snapshot."""
    try:
        hosts = (claimed_host(origin_first), claimed_host(origin_second))
        if hosts[0] == hosts[1]:
            raise InventoryError("Distinct claimed provider hosts required")
        m = assess_snapshot(mint, mint_snapshot)
    except (SnapshotError, ReconciliationError) as exc:
        raise InventoryError(str(exc)) from exc
    a, b = parse_inventory(mint, first), parse_inventory(mint, second)
    if first == second:
        raise InventoryError("Identical saved scans do not establish independent evidence")
    if max(m["snapshot_slot"], a["slot"], b["slot"]) - min(
            m["snapshot_slot"], a["slot"], b["slot"]) > MAX_SLOT_GAP:
        raise InventoryError("Mint and inventory slots too far apart")
    if a["accounts"] != b["accounts"]:
        missing_a = set(b["accounts"]) - set(a["accounts"])
        missing_b = set(a["accounts"]) - set(b["accounts"])
        if missing_a or missing_b:
            raise InventoryError(
                f"Different token account sets: missing in first={len(missing_a)}, "
                f"missing in second={len(missing_b)}"
            )
        raise InventoryError("Token balances, authorities, delegation or frozen states conflict")
    expected = int(m["raw_supply_atomic"])
    if a["sum_atomic"] != expected or b["sum_atomic"] != expected:
        raise InventoryError(
            "Sum of listed token-account amounts does not match mint supply"
        )
    account_set = a["accounts"]
    owners = {a["owner"] for a in account_set.values()}
    # Counts are observational. No address is classified as founder/treasury.
    return {
        "mint_requested": mint,
        "mint_snapshot_slot": m["snapshot_slot"],
        "inventory_slots": [a["slot"], b["slot"]],
        "claimed_provider_hosts": list(hosts),
        "listed_token_accounts": len(account_set),
        "distinct_owner_addresses": len(owners),
        "frozen_token_accounts": sum(v["state"] == "frozen" for v in account_set.values()),
        "delegated_token_accounts": sum(v["delegate"] is not None for v in account_set.values()),
        "listed_balance_total_atomic": str(a["sum_atomic"]),
        "mint_snapshot_supply_atomic": m["raw_supply_atomic"],
        "mint_authority_from_snapshot": m["mint_authority"],
        "freeze_authority_from_snapshot": m["freeze_authority"],
        "matching_listed_account_records": True,
        "listed_balances_match_snapshot_supply": True,
        "offline_consistency_passed": True,
        "rpc_provenance_authenticated": False,
        "scan_filter_and_completeness_proven": False,
        "live_chain_state_verified": False,
        "beneficial_owner_or_treasury_identity_proven": False,
        "founder_vesting_funded_or_deployed": False,
        "sale_or_issuance_authorized": False,
        "note": (
            "Neither identical records nor balance equality proves completeness. "
            "Only externally authenticated RPCs, verified creation records and "
            "independently corroborated holder/authority identities can do so."
        ),
    }


def _read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise InventoryError("Unable to read JSON snapshot: " + str(exc)) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mint", required=True)
    parser.add_argument("--mint-json", required=True, type=Path)
    parser.add_argument("--first-accounts", required=True, type=Path)
    parser.add_argument("--second-accounts", required=True, type=Path)
    parser.add_argument("--first-origin", required=True)
    parser.add_argument("--second-origin", required=True)
    args = parser.parse_args(argv)
    try:
        if args.first_accounts.resolve() == args.second_accounts.resolve():
            raise InventoryError("Two distinct account snapshot files required")
        output = reconcile_inventory(
            args.mint, _read(args.mint_json), _read(args.first_accounts),
            _read(args.second_accounts), args.first_origin, args.second_origin,
        )
    except InventoryError as exc:
        print(json.dumps({
            "offline_consistency_passed": False,
            "sale_or_issuance_authorized": False, "error": str(exc)
        }, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
