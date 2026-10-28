#!/usr/bin/env python3
"""Offline Step 18 mFRG account-purpose reconciliation; never signs or sends RPC."""
import argparse
import json
import sys

BUDGETS = {
    "fundraising": 50_000_000, "operations": 100_000_000,
    "ecosystem": 100_000_000, "staking_rewards": 85_000_000,
    "liquidity": 60_000_000, "engineering_security": 65_000_000,
    "founder_unrestricted": 15_000_000, "founder_vesting": 15_000_000,
    "emergency": 10_000_000,
}
UNIT = 1_000_000
TOTAL = 500_000_000 * UNIT

class ReconciliationError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise ReconciliationError(message)

def reconcile(document):
    require(isinstance(document, dict), "document must be an object")
    require(document.get("schema_version") == 1, "schema_version must equal 1")
    require(document.get("network") == "solana-mainnet-beta", "network must be mainnet-beta")
    require(document.get("token_program") == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", "original SPL Token Program required")
    require(document.get("decimals") == 6 and type(document.get("decimals")) is int, "six decimals required")
    mint = document.get("mint")
    require(isinstance(mint, str) and len(mint) >= 32 and len(mint) <= 44 and mint != "9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw", "real mainnet mint address required; devnet test mint forbidden")
    require(isinstance(document.get("initialization_signature"), str) and len(document["initialization_signature"]) >= 64, "initialization signature required")
    accounts = document.get("accounts")
    require(isinstance(accounts, list) and accounts, "nonempty holder inventory required")
    seen = set()
    totals = {key: 0 for key in BUDGETS}
    unassigned = 0
    for index, item in enumerate(accounts):
        require(isinstance(item, dict), f"account {index} must be an object")
        address = item.get("token_account")
        require(isinstance(address, str) and 32 <= len(address) <= 44, f"account {index} missing token account pubkey")
        require(address not in seen, f"duplicate token account {address}")
        seen.add(address)
        amount = item.get("amount_atomic")
        require(type(amount) is int and amount >= 0, f"invalid atomic balance for {address}")
        purpose = item.get("purpose")
        require(purpose in BUDGETS or purpose == "unassigned", f"invalid purpose on {address}")
        # Self-description alone is insufficient to certify a treasury allocation.
        if purpose in BUDGETS:
            require(item.get("owner_attestation_verified") is True, f"no independently verified owner attestation on {address}")
            require(item.get("governance_authorization_verified") is True, f"no independently verified governance authorization on {address}")
            require(item.get("beneficial_owner_verified") is True, f"no independently verified beneficial owner on {address}")
            totals[purpose] += amount
        else:
            unassigned += amount
    supply = document.get("mint_supply_atomic")
    require(type(supply) is int and supply >= 0, "mint_supply_atomic must be a nonnegative integer")
    require(sum(totals.values()) + unassigned == supply, "holder amounts do not conserve reported mint supply")
    require(supply <= TOTAL, "reported supply exceeds policy maximum")
    for purpose, tokens in BUDGETS.items():
        require(totals[purpose] <= tokens * UNIT, f"{purpose} exceeds planned budget")
    # Even a valid JSON attestation manifest cannot prove signatures or RPC honesty.
    return {
        "status": "OFFLINE_ACCOUNTING_ONLY_NOT_ONCHAIN_PROOF",
        "reported_supply_atomic": supply,
        "target_policy_supply_atomic": TOTAL,
        "allocated_atomic_by_purpose": totals,
        "unassigned_atomic": unassigned,
        "fully_funded_purposes": [p for p, n in totals.items() if n == BUDGETS[p] * UNIT],
        "claims_cryptographically_verified_by_this_script": False,
        "external_rpc_and_owner_evidence_verified_by_this_script": False,
        "sale_authorized": False,
        "treasury_release_authorized": False,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="owner-prepared JSON with independently verified attestations; no secrets")
    args = parser.parse_args()
    try:
        with open(args.manifest, encoding="utf-8") as f:
            result = reconcile(json.load(f))
        print(json.dumps(result, indent=2, sort_keys=True))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
