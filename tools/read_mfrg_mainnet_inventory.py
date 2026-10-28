#!/usr/bin/env python3
"""Opt-in READ-ONLY live mainnet SPL token-account inventory cross-check.

Only getGenesisHash/getAccountInfo/getTransaction (from the existing provenance
gate) and getProgramAccounts RPC reads are used. No signing, key handling,
payments, file writes, transaction submission or state changes.
Account lists >2MB are intentionally rejected rather than silently truncated.
Even if the checks pass, provider independence and beneficial ownership are
NOT authenticated by a response alone.
"""
from __future__ import annotations

import argparse
import json
import sys

from read_mfrg_mainnet_provenance import (
    LiveReadError, assess as provenance_assess,
    exact_https_origin, rpc_call,
)
from reconcile_mfrg_mint_snapshots import reconcile as mint_compare, ReconciliationError
from reconcile_mfrg_token_accounts import (
    reconcile_inventory, InventoryError, MAX_ACCOUNTS,
)
from verify_mfrg_mint_snapshot import TOKEN_PROGRAM

SPL_TOKEN_ACCOUNT_BYTES = 165


def account_params(mint):
    """Exact standard SPL mint filter, never unfiltered global account scans."""
    return [TOKEN_PROGRAM, {
        "encoding": "jsonParsed",
        "commitment": "finalized",
        "withContext": True,
        "filters": [
            {"dataSize": SPL_TOKEN_ACCOUNT_BYTES},
            {"memcmp": {"offset": 0, "bytes": mint}},
        ],
    }]


def assess(mint, signature, url_a, url_b, rpc=rpc_call):
    """Run existing genesis+initialization gate and then exact inventory scans."""
    provenance = provenance_assess(mint, signature, url_a, url_b, rpc=rpc)
    hosts = [exact_https_origin(url_a), exact_https_origin(url_b)]
    snapshots = []
    for host in hosts:
        # Fresh mint snapshots are needed so account scans may be compared at
        # approximately the same finalized slots, rather than using stale
        # initialization-era supply or the previous provenance query's data.
        mint_reply = rpc(host, "getAccountInfo", [
            mint, {"encoding": "jsonParsed", "commitment": "finalized"}
        ], mint)
        account_reply = rpc(host, "getProgramAccounts", account_params(mint),
                            mint + ":inventory")
        snapshots.append((mint_reply, account_reply))
    try:
        mint_check = mint_compare(
            mint, snapshots[0][0], snapshots[1][0], url_a, url_b
        )
        inventory_check = reconcile_inventory(
            mint, snapshots[0][0], snapshots[0][1], snapshots[1][1],
            url_a, url_b
        )
    except (ReconciliationError, InventoryError) as exc:
        raise LiveReadError("Holder inventory reconciliation blocked: " + str(exc)) from exc
    if mint_check["matching_raw_supply_atomic"] != provenance["mint_supply_atomic"]:
        raise LiveReadError("Mint supply changed between provenance and inventory reads")
    if inventory_check["listed_balance_total_atomic"] != provenance["mint_supply_atomic"]:
        raise LiveReadError("Account inventory sum and verified-path mint read differ")
    return {
        "requested_mint": mint,
        "existing_creation_transaction_signature": signature,
        "reported_genesis": provenance["reported_genesis"],
        "genesis_matches_mainnet_expected_on_both_rpc_endpoints": True,
        "queried_rpc_hostnames": hosts,
        "provenance_mint_snapshot_slots": provenance["mint_snapshot_slots"],
        "inventory_mint_snapshot_slots": mint_check["snapshot_slots"],
        "inventory_account_snapshot_slots": inventory_check["inventory_slots"],
        "mint_initialization_slot": provenance["mint_initialization_slot"],
        "matching_raw_supply_atomic": inventory_check["listed_balance_total_atomic"],
        "listed_token_accounts": inventory_check["listed_token_accounts"],
        "distinct_listed_owner_addresses": inventory_check["distinct_owner_addresses"],
        "listed_frozen_accounts": inventory_check["frozen_token_accounts"],
        "listed_delegated_accounts": inventory_check["delegated_token_accounts"],
        "mint_authority": mint_check["matching_mint_authority"],
        "freeze_authority": mint_check["matching_freeze_authority"],
        "live_readonly_rpc_consistency_passed": True,
        "account_scan_mint_filter_required": True,
        "standard_spl_account_size_filter": SPL_TOKEN_ACCOUNT_BYTES,
        "configured_max_account_count": MAX_ACCOUNTS,
        "per_response_limit_bytes": 2_000_000,
        "rpc_answers_cryptographically_authenticated": False,
        "rpc_provider_independence_proven": False,
        "transaction_signature_cryptographically_verified": False,
        "account_scan_completeness_independently_proven": False,
        "project_mint_issuer_or_beneficial_owner_verified": False,
        "nine_treasury_account_ownership_verified": False,
        "founder_vesting_deployed_or_funded": False,
        "sale_or_issuance_authorized": False,
        "next_gate": (
            "Corroborate mint and inventory against independent trusted explorers "
            "and authorized issuer records; verify program/multisig controls and "
            "beneficial owner identity before any financial action."
        ),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mint", required=True,
                   help="Owner-authenticated EXISTING Solana mainnet mFRG mint")
    p.add_argument("--signature", required=True,
                   help="Existing mainnet initializeMint/initializeMint2 transaction")
    p.add_argument("--rpc-one", required=True,
                   help="First HTTPS RPC origin, no keys or API paths")
    p.add_argument("--rpc-two", required=True,
                   help="Independent second HTTPS RPC origin, no keys or API paths")
    args = p.parse_args(argv)
    try:
        result = assess(args.mint, args.signature, args.rpc_one, args.rpc_two)
    except LiveReadError as exc:
        print(json.dumps({
            "live_readonly_rpc_consistency_passed": False,
            "sale_or_issuance_authorized": False,
            "error": str(exc),
        }, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
