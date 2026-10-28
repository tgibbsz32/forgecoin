#!/usr/bin/env python3
"""Offline, non-transactional mFRG treasury and founder-vesting preflight.

This tool reads *planning* JSON from the local repository. It does not use RPC,
wallet keys, create accounts, perform transfers, or attest an on-chain balance.
A hypothetical launch date is simulation input, never a release authorization.
"""
from __future__ import annotations

import argparse
import calendar
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "apps/desktop/config/miniFORGE.mainnet.plan.json"
STATUS_PATH = ROOT / "docs/sale-status.json"
REGISTRY_PATH = ROOT / "docs/mfrg-treasury-registry.template.json"
DECIMALS = 6
FACTOR = 10 ** DECIMALS
SUPPLY = 500_000_000
FOUNDERS_IMMEDIATE = 15_000_000
FOUNDERS_DEFERRED = 15_000_000
MONTHLY_DEFERRED = 625_000
MONTHS = range(13, 37)
PILOT_MAX = 5_000_000
EXPECTED = {
    "fundraising": 50_000_000,
    "operations": 100_000_000,
    "ecosystem": 100_000_000,
    "staking": 85_000_000,
    "liquidity": 60_000_000,
    "engineering_security": 65_000_000,
    "founder_immediate": 15_000_000,
    "founder_deferred_team_label": 15_000_000,
    "emergency": 10_000_000,
}
PERIODS = {
    "year_1": 74_000_000, "years_2_3": 95_000_000,
    "years_4_10": 117_000_000, "years_11_20": 113_000_000,
    "years_21_30": 101_000_000,
}


class PreflightError(ValueError):
    """The local plan, readiness registry or time input is not valid."""


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise PreflightError(f"Unable to read valid JSON from {path}: {error}") from error


def parse_utc(value: str) -> datetime:
    """Require an explicit UTC timestamp, no local/naive wall clock."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise PreflightError("Require ISO-8601 UTC date-time, e.g. 2026-11-01T00:00:00Z") from error
    if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
        raise PreflightError("Time input must specify UTC explicitly (Z or +00:00)")
    return dt.astimezone(timezone.utc)


def add_calendar_months(anchor: datetime, months: int) -> datetime:
    """Use original launch timestamp as anchor; end-of-month clamps do not drift."""
    if anchor.tzinfo is None or anchor.utcoffset() != timedelta(0) or months < 0:
        raise PreflightError("Launch date must be UTC and months nonnegative")
    month_index = (anchor.year * 12 + anchor.month - 1) + months
    year, zero_month = divmod(month_index, 12)
    month = zero_month + 1
    if year > 9999:
        raise PreflightError("Vesting timestamp is outside calendar range")
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return anchor.replace(year=year, month=month, day=day)


def founder_vesting_schedule(launch: datetime):
    """Months 13..36 mean *end* of each numbered month since token launch.

    At T0+24 months exactly 12 installments have vested; at T0+36, all 24.
    """
    return [
        {
            "month_number": month,
            "release_utc": add_calendar_months(launch, month).isoformat().replace("+00:00", "Z"),
            "tranche_mfrg": MONTHLY_DEFERRED,
            "cumulative_deferred_mfrg": (month - 12) * MONTHLY_DEFERRED,
            "cumulative_founder_available_mfrg": FOUNDERS_IMMEDIATE + (month - 12) * MONTHLY_DEFERRED,
        }
        for month in MONTHS
    ]


def founder_available(launch: datetime, at: datetime):
    if at < launch:
        return {"immediate_mfrg": 0, "vested_deferred_mfrg": 0,
                "total_available_mfrg": 0, "vested_installments": 0}
    vested_months = sum(at >= add_calendar_months(launch, month) for month in MONTHS)
    vested = vested_months * MONTHLY_DEFERRED
    return {
        "immediate_mfrg": FOUNDERS_IMMEDIATE,
        "vested_deferred_mfrg": vested,
        "total_available_mfrg": FOUNDERS_IMMEDIATE + vested,
        "vested_installments": vested_months,
    }


def exact_nonnegative_integer_string(value, label):
    if (not isinstance(value, str) or not value.isascii()
            or not value.isdecimal()):
        raise PreflightError(label + " must be an exact decimal integer string")
    return int(value)


def assess_plan(plan: dict, status: dict, registry: dict):
    if not isinstance(plan, dict) or not isinstance(status, dict) or not isinstance(registry, dict):
        raise PreflightError("All inputs must be JSON objects")
    if (plan.get("configuration_type") != "NON_TRANSACTIONAL_PLANNING_DATA_ONLY"
            or plan.get("network") != "mainnet-beta" or plan.get("decimals") != DECIMALS):
        raise PreflightError("Unexpected planning schema, token decimals or network")
    supply_ui = exact_nonnegative_integer_string(plan.get("target_supply_ui"), "target_supply_ui")
    supply_atomic = exact_nonnegative_integer_string(plan.get("target_supply_atomic"), "target_supply_atomic")
    if supply_ui != SUPPLY or supply_atomic != SUPPLY * FACTOR:
        raise PreflightError("Total supply in planning data is inconsistent")
    allocations = plan.get("allocations")
    if not isinstance(allocations, list) or len(allocations) != 9:
        raise PreflightError("Exactly nine distinct mFRG allocations required")
    seen = {}
    for a in allocations:
        if not isinstance(a, dict) or a.get("id") in seen:
            raise PreflightError("Duplicate or invalid allocation identifier")
        key = a.get("id")
        if key not in EXPECTED:
            raise PreflightError("Unexpected allocation identifier")
        if (exact_nonnegative_integer_string(a.get("tokens_ui"), key + ".tokens_ui") != EXPECTED[key]
                or exact_nonnegative_integer_string(a.get("amount_atomic"), key + ".amount_atomic") != EXPECTED[key] * FACTOR):
            raise PreflightError("Allocation differs from authorized tokenomics: " + key)
        if a.get("account_address") is not None or a.get("custody_authority") is not None:
            raise PreflightError("Planning file cannot silently provision treasury addresses")
        releases = a.get("release_ceiling_by_period_mfrg")
        if not isinstance(releases, dict) or set(releases) != set(PERIODS):
            raise PreflightError("Release periods must match the nine-bucket schedule")
        if (any(type(v) is not int or v < 0 for v in releases.values())
                or sum(releases.values()) != EXPECTED[key]):
            raise PreflightError("Release ceilings are not conserved for " + key)
        seen[key] = a
    if set(seen) != set(EXPECTED) or sum(EXPECTED.values()) != SUPPLY:
        raise PreflightError("The nine allocation amounts must sum to exactly 500M")
    for period, required in PERIODS.items():
        actual = sum(a["release_ceiling_by_period_mfrg"][period] for a in allocations)
        if actual != required or plan.get("release_schedule_total_by_period_mfrg", {}).get(period) != required:
            raise PreflightError("Period release ceilings do not reconcile: " + period)

    founder = plan.get("founder")
    if (not isinstance(founder, dict) or founder.get("immediate_id") != "founder_immediate"
            or founder.get("deferred_id") != "founder_deferred_team_label"
            or founder.get("beneficial_owner") != "founder (both 3% allocations)"
            or founder.get("monthly_vesting_first_month") != 13
            or founder.get("monthly_vesting_last_month") != 36
            or exact_nonnegative_integer_string(founder.get("monthly_tokens_ui"), "founder.monthly_tokens_ui") != MONTHLY_DEFERRED
            or exact_nonnegative_integer_string(founder.get("monthly_amount_atomic"), "founder.monthly_amount_atomic") != MONTHLY_DEFERRED * FACTOR
            or exact_nonnegative_integer_string(founder.get("total_tokens_ui"), "founder.total_tokens_ui") != 30_000_000):
        raise PreflightError("Founder 6% beneficial ownership / vesting changed")
    if 24 * MONTHLY_DEFERRED != FOUNDERS_DEFERRED:
        raise PreflightError("Founder vesting arithmetic incorrect")
    funding = plan.get("fundraising")
    if (not isinstance(funding, dict)
            or exact_nonnegative_integer_string(funding.get("pilot_inventory_ui"), "pilot_inventory_ui") != PILOT_MAX
            or exact_nonnegative_integer_string(funding.get("total_inventory_ui"), "total_inventory_ui") != 50_000_000
            or funding.get("checkout_enabled") is not False):
        raise PreflightError("50M lifetime / 5M pilot fundraising controls changed")
    for key in ("is_issuance_authorized", "is_sale_authorized", "is_staking_authorized",
                "is_liquidity_authorized", "fixed_cap_enforced", "allocation_completed"):
        if plan.get(key) is not False:
            raise PreflightError("Production activation flag cannot be true: " + key)
    if (plan.get("network_mint_address") is not None or
            plan.get("mint_authority_status") != "unverified"):
        raise PreflightError("Unverified planning data must not claim mainnet mint")
    for key in ("sale_enabled", "quotes_enabled", "payments_enabled", "fulfillment_enabled"):
        if status.get(key) is not False:
            raise PreflightError("Public sale/status remains disabled: " + key)
    if (status.get("token_mainnet_mint") is not None or status.get("sale_price_usdc") is not None
            or status.get("allocation_mfrg") != EXPECTED
            or status.get("initial_pilot_mfrg") != PILOT_MAX
            or status.get("founder_beneficial_total_mfrg") != 30_000_000):
        raise PreflightError("Public sale JSON and treasury plan conflict")

    # The sample registry deliberately must never contain any live chain
    # addresses, claims of funding, or a release/authorization switch.
    if (registry.get("schema") != "mfrg-treasury-readiness-v1"
            or registry.get("mode") != "NON_TRANSACTIONAL_TEMPLATE_ONLY"
            or registry.get("network_mint_address") is not None
            or registry.get("launch_utc") is not None
            or registry.get("mint_supply_target_atomic") != str(SUPPLY * FACTOR)
            or registry.get("production_actions_allowed") is not False):
        raise PreflightError("Registry template must remain inert and address-free")
    proposed_founder = registry.get("founder")
    if (not isinstance(proposed_founder, dict)
            or proposed_founder.get("unlocked_mfrg_at_actual_launch") != FOUNDERS_IMMEDIATE
            or proposed_founder.get("deferred_team_labeled_founder_benefit_mfrg") != FOUNDERS_DEFERRED
            or proposed_founder.get("first_release_month") != 13
            or proposed_founder.get("last_release_month") != 36
            or proposed_founder.get("monthly_release_mfrg") != MONTHLY_DEFERRED
            or proposed_founder.get("contract_address") is not None
            or proposed_founder.get("beneficiary_wallet") is not None
            or proposed_founder.get("actual_launch_timestamp_verified") is not False
            or proposed_founder.get("vesting_funded_verified") is not False):
        raise PreflightError("Founder vesting registry must be unconfigured and unfunded")
    proceeds = registry.get("external_proceeds")
    if (not isinstance(proceeds, dict) or proceeds.get("treasury_account") is not None
            or proceeds.get("signers_verified") is not False
            or proceeds.get("balance_verified") is not False):
        raise PreflightError("Crypto proceeds registry cannot imply funded accounts")
    gates = registry.get("verification")
    required = (
        "mint_authenticated", "holder_inventory_reconciled", "multisig_signers_approved",
        "vesting_contract_audited", "treasury_funding_verified",
        "legal_distributions_approved", "sale_contract_audited"
    )
    if not isinstance(gates, dict) or set(gates) != set(required) or any(v is not False for v in gates.values()):
        raise PreflightError("Registry must not claim approvals or on-chain verification")
    accounts = registry.get("accounts")
    if not isinstance(accounts, list) or len(accounts) != 9:
        raise PreflightError("Registry requires nine independent account templates")
    seen_registry = set()
    for a in accounts:
        if not isinstance(a, dict):
            raise PreflightError("Invalid registry account")
        ident = a.get("id")
        if ident not in EXPECTED or ident in seen_registry:
            raise PreflightError("Duplicate or unknown registry account")
        seen_registry.add(ident)
        if (a.get("allocation_mfrg") != EXPECTED[ident] or
                a.get("allocation_atomic") != str(EXPECTED[ident] * FACTOR) or
                any(a.get(k) is not None for k in ("token_account", "owner_authority", "verified_balance_atomic")) or
                a.get("funded_verified") is not False):
            raise PreflightError("Proposed account cannot be represented as funded: " + ident)
    if seen_registry != set(EXPECTED):
        raise PreflightError("Registry purpose set does not match allocations")
    return {
        "intended_mfrg_supply": SUPPLY,
        "target_supply_atomic": str(SUPPLY * FACTOR),
        "nine_allocations": {k: EXPECTED[k] for k in EXPECTED},
        "founder_total_beneficial_mfrg": FOUNDERS_IMMEDIATE + FOUNDERS_DEFERRED,
        "founder_immediate_at_hypothetical_launch_mfrg": FOUNDERS_IMMEDIATE,
        "founder_deferred_monthly_mfrg": MONTHLY_DEFERRED,
        "founder_deferred_release_months": [13, 36],
        "pilot_limit_mfrg": PILOT_MAX,
        "lifetime_fundraising_limit_mfrg": 50_000_000,
        "plan_reconciled": True,
        "all_nine_accounts_funded_verified": False,
        "mint_independently_verified": False,
        "sale_or_issuance_authorized": False,
        "real_launch_scheduled": False,
        "next_gate": "Independently authenticate mFRG mainnet mint and treasury holder snapshot; approve signer/vesting/legal program before any tokens move.",
    }


def build_report(plan, status, registry, *, hypothetical_launch=None, as_of=None):
    result = assess_plan(plan, status, registry)
    if hypothetical_launch is None:
        if as_of is not None:
            raise PreflightError("--as-of-utc requires --hypothetical-launch-utc")
        result["simulation"] = None
        return result
    launch = parse_utc(hypothetical_launch)
    at = parse_utc(as_of) if as_of else launch
    schedule = founder_vesting_schedule(launch)
    result["simulation"] = {
        "hypothetical_only": True,
        "launch_utc": launch.isoformat().replace("+00:00", "Z"),
        "as_of_utc": at.isoformat().replace("+00:00", "Z"),
        "founder_if_validly_issued_and_funded": founder_available(launch, at),
        "deferred_vesting_installments": schedule,
        "actual_launch_or_issuance_confirmed": False,
    }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hypothetical-launch-utc",
                        help="UTC date/time for NON-BINDING founder vesting simulation only")
    parser.add_argument("--as-of-utc",
                        help="UTC comparison time; requires hypothetical launch time")
    args = parser.parse_args(argv)
    try:
        report = build_report(read_json(PLAN_PATH), read_json(STATUS_PATH),
                              read_json(REGISTRY_PATH),
                              hypothetical_launch=args.hypothetical_launch_utc,
                              as_of=args.as_of_utc)
    except PreflightError as exc:
        print(json.dumps({"plan_reconciled": False, "sale_or_issuance_authorized": False,
                          "error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
