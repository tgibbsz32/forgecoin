#!/usr/bin/env python3
"""Offline SPL multisig structural preflight and PDA fail-closed routing.

Never calls RPC or signs anything. No source is authenticated by a JSON file.
A matching 3/5 or 4/5 signer list is NOT proof of beneficial independence,
multisig governance consent, actual treasury funding, or sale authorization.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from verify_mfrg_mint_snapshot import (
    TOKEN_PROGRAM, DECIMALS, SnapshotError, validate_pubkey, assess_snapshot
)
from reconcile_mfrg_token_accounts import (
    parse_inventory, InventoryError, MAX_SLOT_GAP
)
from mfrg_treasury_vesting_preflight import EXPECTED, FACTOR

MULTISIG_PURPOSES = frozenset({
    "fundraising", "operations", "ecosystem", "staking",
    "liquidity", "engineering_security", "emergency"
})
FOUNDER_PURPOSES = frozenset({
    "founder_immediate", "founder_deferred_team_label"
})
DEVNET_MINT = "9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw"


class AuthorityError(ValueError):
    """Invalid or insufficient custody authority evidence."""


def pubkey(value, name):
    try:
        return validate_pubkey(value)
    except SnapshotError as error:
        raise AuthorityError(f"{name}: {error}") from error


def source_account(authority, payload):
    if not isinstance(payload, dict) or payload.get("id") != authority:
        raise AuthorityError("AccountInfo RPC id must match requested multisig authority")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise AuthorityError("Missing accountInfo result")
    context = result.get("context")
    if not isinstance(context, dict) or type(context.get("slot")) is not int or context["slot"] <= 0:
        raise AuthorityError("Missing positive accountInfo context slot")
    account = result.get("value")
    if not isinstance(account, dict):
        raise AuthorityError("Multisig address account does not exist in supplied data")
    if account.get("owner") != TOKEN_PROGRAM or account.get("executable") is not False:
        raise AuthorityError("Not a standard SPL Token program-owned multisig account")
    data = account.get("data")
    if (not isinstance(data, dict) or data.get("program") != "spl-token"
            or not isinstance(data.get("parsed"), dict)
            or data["parsed"].get("type") != "multisig"):
        raise AuthorityError("Account is not parsed as standard SPL multisig")
    info = data["parsed"].get("info")
    if not isinstance(info, dict) or info.get("isInitialized") is not True:
        raise AuthorityError("SPL multisig is uninitialized or missing parsed info")
    required = info.get("numRequiredSigners")
    count = info.get("numValidSigners")
    signers = info.get("signers")
    if (type(required) is not int or type(count) is not int
            or not isinstance(signers, list) or not 1 <= required <= count <= 11
            or len(signers) != count):
        raise AuthorityError("Invalid m-of-n parsed signer counts")
    for s in signers:
        pubkey(s, "SPL multisig signer")
    if len(set(signers)) != count:
        raise AuthorityError("Multisig signer public keys must be distinct")
    return context["slot"], required, signers


def assess(manifest, mint_snapshot, inventory_snapshot, authority_snapshot=None):
    if not isinstance(manifest, dict) or manifest.get("schema") != "mfrg-custody-preflight-v1":
        raise AuthorityError("Unexpected or missing custody manifest schema")
    if manifest.get("network") != "mainnet-beta":
        raise AuthorityError("Require mainnet-beta as untrusted intended network label")
    mint = pubkey(manifest.get("mint"), "mint")
    if mint == DEVNET_MINT:
        raise AuthorityError("Historic devnet test mint not accepted as mainnet")
    try:
        mint_info = assess_snapshot(mint, mint_snapshot)
        inventory = parse_inventory(mint, inventory_snapshot)
    except (SnapshotError, InventoryError) as error:
        raise AuthorityError(str(error)) from error
    claim = manifest.get("claim")
    if not isinstance(claim, dict):
        raise AuthorityError("Require exactly one custody claim")
    purpose = claim.get("purpose")
    if purpose not in EXPECTED:
        raise AuthorityError("Unknown or unauthorised mFRG allocation category")
    token = pubkey(claim.get("token_account"), "token account")
    authority = pubkey(claim.get("owner_authority"), "claimed authority")
    observed = inventory["accounts"].get(token)
    if observed is None or observed["owner"] != authority:
        raise AuthorityError("Claimed authority does not match listed token account owner")
    if observed["raw"] == 0 or observed["raw"] > EXPECTED[purpose] * FACTOR:
        raise AuthorityError("Listed balance is zero or exceeds allocation ceiling")
    if (observed["state"] != "initialized" or observed["delegate"] is not None
            or observed["close_authority"] is not None):
        raise AuthorityError("Frozen, delegated or close-authority custody requires separate review")
    common = {
        "mint": mint,
        "purpose": purpose,
        "listed_token_account": token,
        "listed_owner_authority": authority,
        "listed_balance_atomic": str(observed["raw"]),
        "mint_snapshot_slot": mint_info["snapshot_slot"],
        "inventory_snapshot_slot": inventory["slot"],
        "rpc_source_authenticated": False,
        "mint_creation_authenticated": False,
        "inventory_completeness_verified": False,
        "beneficial_owner_or_signer_independence_verified": False,
        "owner_approved_multisig": False,
        "treasury_funded_on_chain_verified": False,
        "vesting_contract_audited_or_deployed": False,
        "sale_or_issuance_authorized": False,
    }
    kind = claim.get("authority_type")
    if kind == "program_pda":
        program = pubkey(claim.get("program_id"), "PDA program")
        # Do NOT infer a real PDA from a string and call it validated. Correct
        # derivation also needs audited exact byte seeds, canonical bump, and
        # a trusted program/upgrade-authority record.
        if authority_snapshot is not None:
            raise AuthorityError("PDA must not be verified via SPL multisig snapshot")
        if purpose not in FOUNDER_PURPOSES | MULTISIG_PURPOSES:
            raise AuthorityError("Unexpected PDA purpose")
        return {
            **common, "authority_type": "program_pda",
            "claimed_program_id": program,
            "decision": "BLOCKED_REQUIRE_AUTHENTICATED_PDA_DERIVATION_AND_PROGRAM_AUDIT",
            "pda_derivation_verified": False,
            "upgrade_authority_verified": False,
            "release_schedule_enforced_on_chain": False,
            "note": "A PDA has no private key and cannot provide Step 13 Ed25519 consent. Real proof needs exact seeds/bump, program ID, verified deployed bytecode, upgrade authority and program-policy audit.",
        }
    if kind != "spl_multisig":
        raise AuthorityError("Unsupported authority type; choose spl_multisig or program_pda")
    if purpose not in MULTISIG_PURPOSES:
        raise AuthorityError("Founder allocations require beneficiary and audited vesting-specific evidence")
    if authority_snapshot is None:
        raise AuthorityError("SPL multisig requires saved getAccountInfo authority snapshot")
    slot, required, signers = source_account(authority, authority_snapshot)
    expected = 4 if purpose == "emergency" else 3
    if required != expected or len(signers) != 5:
        raise AuthorityError(f"Proposed {purpose} multisig requires {expected}-of-5 exactly")
    declared = claim.get("expected_signer_keys")
    if not isinstance(declared, list) or len(declared) != 5:
        raise AuthorityError("Expected signer list must have exactly five public keys")
    for signer in declared:
        pubkey(signer, "planned multisig signer")
    if len(set(declared)) != 5 or set(signers) != set(declared):
        raise AuthorityError("Declared signer set conflicts with parsed SPL multisig")
    if (max(mint_info["snapshot_slot"], inventory["slot"], slot) -
            min(mint_info["snapshot_slot"], inventory["slot"], slot) > MAX_SLOT_GAP):
        raise AuthorityError("Mint, inventory and multisig account snapshots too far apart")
    return {
        **common, "authority_type": "spl_multisig",
        "decision": "OFFLINE_SPL_MULTISIG_STRUCTURE_CONSISTENT_ONLY",
        "num_required_signers": required,
        "num_valid_signers": len(signers),
        "listed_signers": signers,
        "authority_snapshot_slot": slot,
        "multisig_structure_matches_proposal": True,
        "signer_control_proven": False,
        "signer_policy_approved": False,
        "note": "Matching 3/5 or 4/5 parsed keys is not proof who holds them, that signers are independent people, or that proposed governance and custody are legally approved.",
    }


def read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise AuthorityError(f"Invalid JSON file {path}: {error}") from error


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--mint-json", required=True, type=Path)
    p.add_argument("--inventory-json", required=True, type=Path)
    p.add_argument("--authority-json", type=Path, help="Only for SPL multisig")
    args = p.parse_args(argv)
    try:
        report = assess(
            read(args.manifest), read(args.mint_json), read(args.inventory_json),
            read(args.authority_json) if args.authority_json else None
        )
    except AuthorityError as error:
        print(json.dumps({
            "custody_structure_valid": False,
            "sale_or_issuance_authorized": False,
            "error": str(error),
        }, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
