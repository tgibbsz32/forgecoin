#!/usr/bin/env python3
"""Explicitly opt-in, read-only Solana mainnet genesis and mint/tx cross-check.

Only sends getGenesisHash, getAccountInfo and getTransaction RPC POST queries.
Never signs, creates, moves, freezes, mints, pays, logs wallet secrets or writes
files. TLS hostname validation verifies connection to an operator-specified host,
not independence, legal issuer identity, chain consensus or beneficial custody.
"""
from __future__ import annotations
import argparse
import http.client
import ipaddress
import json
import ssl
import sys
from urllib.parse import urlsplit

from verify_mfrg_mint_snapshot import SnapshotError, validate_pubkey
from verify_mfrg_mint_initialization import report as init_report, InitializationError, signature_key
from reconcile_mfrg_mint_snapshots import reconcile as mint_compare, ReconciliationError

MAINNET_GENESIS = "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d"
MAX_REPLY_BYTES = 2_000_000
TIMEOUT_SECONDS = 12


class LiveReadError(ValueError):
    pass


def exact_https_origin(url):
    """Avoid credentials, redirect targets, non-HTTPS, paths or private IP literals."""
    if not isinstance(url, str):
        raise LiveReadError("RPC URL must be HTTPS origin")
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise LiveReadError("Invalid RPC URL") from exc
    if (parsed.scheme != "https" or not host or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment
            or parsed.path not in ("", "/") or port not in (None, 443)
            or "." not in host or any(ch.isspace() for ch in host)
            or host.endswith(".local") or host in ("localhost", "localhost.localdomain")):
        raise LiveReadError("Require plain public HTTPS RPC origin (hostname only, no credentials)")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # A hostname is not an IP literal. This branch does not validate DNS
        # resolution or guarantee the provider's organizational independence.
        ip = None
    if ip is not None and not ip.is_global:
        raise LiveReadError("Private or local IP literal not permitted")
    return host.lower().rstrip(".")


def rpc_call(host, method, params, reqid):
    """Injectable single-request transport. No redirects, explicit TLS and size cap."""
    body = json.dumps({
        "jsonrpc": "2.0", "id": reqid, "method": method, "params": params
    }, separators=(",", ":")).encode("utf-8")
    connection = http.client.HTTPSConnection(
        host, 443, timeout=TIMEOUT_SECONDS,
        context=ssl.create_default_context()
    )
    try:
        connection.request("POST", "/", body,
                           headers={"Content-Type": "application/json",
                                    "Accept": "application/json"})
        response = connection.getresponse()
        if response.status != 200:
            raise LiveReadError(f"Read-only RPC {method} failed HTTP {response.status}")
        raw = response.read(MAX_REPLY_BYTES + 1)
        if len(raw) > MAX_REPLY_BYTES:
            raise LiveReadError(f"RPC {method} reply exceeds size cap")
        parsed = json.loads(raw.decode("utf-8"))
        if (not isinstance(parsed, dict) or parsed.get("id") != reqid
                or parsed.get("jsonrpc") != "2.0" or "error" in parsed
                or "result" not in parsed):
            raise LiveReadError(f"RPC {method} returned an error or mismatched response ID")
        return parsed
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        if isinstance(exc, LiveReadError):
            raise
        raise LiveReadError(f"Read-only RPC {method} connection/parse failed: {type(exc).__name__}") from exc
    finally:
        connection.close()


def assess(mint, signature, url_a, url_b, rpc=rpc_call):
    try:
        validate_pubkey(mint)
        signature_key(signature)
    except (SnapshotError, InitializationError) as exc:
        raise LiveReadError(str(exc)) from exc
    if mint == "9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw":
        raise LiveReadError("Historical devnet test mint cannot be mainnet mint")
    hosts = [exact_https_origin(url_a), exact_https_origin(url_b)]
    if hosts[0] == hosts[1]:
        raise LiveReadError("Two distinct independently chosen RPC hosts required")
    snapshots = []
    for host in hosts:
        # Stop immediately if this TLS-connected RPC does not report the
        # known Solana mainnet genesis. Genesis claim alone is not proof.
        chain = rpc(host, "getGenesisHash", [], "mfrg-chain")
        if (not isinstance(chain, dict) or chain.get("result") != MAINNET_GENESIS
                or chain.get("id") != "mfrg-chain"):
            raise LiveReadError("RPC does not report required Solana mainnet genesis")
        mint_reply = rpc(host, "getAccountInfo", [
            mint, {"encoding": "jsonParsed", "commitment": "finalized"}
        ], mint)
        tx_reply = rpc(host, "getTransaction", [
            signature, {"encoding": "jsonParsed", "commitment": "finalized",
                        "maxSupportedTransactionVersion": 0}
        ], signature)
        snapshots.append((mint_reply, tx_reply))
    try:
        mint_evidence = mint_compare(mint, snapshots[0][0], snapshots[1][0],
                                     url_a, url_b)
        initialization = init_report(mint, signature, snapshots[0][1],
                                     snapshots[1][1], snapshots[0][0],
                                     url_a, url_b)
        if mint_evidence["matching_raw_supply_atomic"] != initialization["later_raw_supply_atomic"]:
            raise LiveReadError("Supply reports disagree")
    except (InitializationError, ReconciliationError) as exc:
        raise LiveReadError(str(exc)) from exc
    return {
        "requested_mint": mint, "requested_creation_signature": signature,
        "queried_rpc_hostnames": hosts, "reported_genesis": MAINNET_GENESIS,
        "genesis_matches_mainnet_expected_on_both_rpc_endpoints": True,
        "mint_snapshot_slots": mint_evidence["snapshot_slots"],
        "mint_supply_atomic": mint_evidence["matching_raw_supply_atomic"],
        "mint_authority": mint_evidence["matching_mint_authority"],
        "freeze_authority": mint_evidence["matching_freeze_authority"],
        "mint_initialization_slot": initialization["observed_initialization_slot"],
        "transaction_and_mint_parsed_consistency": True,
        "read_only_rpc_queries_succeeded": True,
        "cryptographic_transaction_signature_verified": False,
        "operator_provider_independence_proven": False,
        "project_issuer_and_beneficial_owner_verified": False,
        "treasury_custody_or_funding_verified": False,
        "sale_or_issuance_authorized": False,
        "note": "Genesis checks authenticate neither RPC truthfulness nor independent providers. Operator must confirm mint creation, issuance and custody with independent trusted explorers, finalized records and actual signer approval.",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mint", required=True, help="Existing owner-sourced mainnet mFRG mint address")
    p.add_argument("--signature", required=True, help="Existing mint initialize tx signature")
    p.add_argument("--rpc-one", required=True, help="Public HTTPS origin only, no API keys")
    p.add_argument("--rpc-two", required=True, help="Different independently selected HTTPS origin")
    args = p.parse_args(argv)
    try:
        out = assess(args.mint, args.signature, args.rpc_one, args.rpc_two)
    except LiveReadError as exc:
        print(json.dumps({"live_read_preflight_passed": False,
                          "sale_or_issuance_authorized": False,
                          "error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
