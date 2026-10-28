#!/usr/bin/env python3
"""Offline mFRG treasury registry, 500M accounting and calendar vesting tests."""
import copy
from datetime import timedelta
import unittest

from mfrg_treasury_vesting_preflight import (
    PLAN_PATH, REGISTRY_PATH, STATUS_PATH,
    MONTHLY_DEFERRED, PreflightError, add_calendar_months,
    assess_plan, build_report, founder_available,
    founder_vesting_schedule, parse_utc, read_json,
)


class TreasuryVestingTests(unittest.TestCase):
    def setUp(self):
        self.plan = read_json(PLAN_PATH)
        self.status = read_json(STATUS_PATH)
        self.registry = read_json(REGISTRY_PATH)

    def test_01_exact_nine_account_500m_distribution(self):
        report = assess_plan(self.plan, self.status, self.registry)
        self.assertEqual(report["intended_mfrg_supply"], 500_000_000)
        self.assertEqual(report["target_supply_atomic"], "500000000000000")
        self.assertEqual(len(report["nine_allocations"]), 9)
        self.assertEqual(sum(report["nine_allocations"].values()), 500_000_000)
        self.assertEqual(report["founder_total_beneficial_mfrg"], 30_000_000)
        self.assertEqual(report["pilot_limit_mfrg"], 5_000_000)
        self.assertEqual(report["lifetime_fundraising_limit_mfrg"], 50_000_000)
        self.assertIs(report["sale_or_issuance_authorized"], False)
        self.assertIs(report["mint_independently_verified"], False)

    def test_02_no_actual_launch_or_funding_claim(self):
        report = build_report(self.plan, self.status, self.registry)
        self.assertIsNone(report["simulation"])
        self.assertIs(report["real_launch_scheduled"], False)
        self.assertIs(report["all_nine_accounts_funded_verified"], False)
        self.assertEqual([v["token_account"] for v in self.registry["accounts"]], [None] * 9)
        self.assertIsNone(self.registry["launch_utc"])
        self.assertIsNone(self.registry["network_mint_address"])

    def test_03_months_13_through_36_exact_founder_ceiling(self):
        t0 = parse_utc("2026-10-28T00:00:00Z")
        installments = founder_vesting_schedule(t0)
        self.assertEqual(len(installments), 24)
        self.assertEqual(installments[0]["month_number"], 13)
        self.assertEqual(installments[0]["release_utc"], "2027-11-28T00:00:00Z")
        self.assertEqual(installments[-1]["month_number"], 36)
        self.assertEqual(installments[-1]["release_utc"], "2029-10-28T00:00:00Z")
        self.assertEqual(sum(p["tranche_mfrg"] for p in installments), 15_000_000)
        self.assertEqual(installments[-1]["cumulative_founder_available_mfrg"], 30_000_000)

    def test_04_month_12_to_13_no_early_release(self):
        t0 = parse_utc("2026-10-28T00:00:00Z")
        first = add_calendar_months(t0, 13)
        at_t0 = founder_available(t0, t0)
        self.assertEqual(at_t0["total_available_mfrg"], 15_000_000)
        self.assertEqual(founder_available(t0, add_calendar_months(t0, 12))["vested_deferred_mfrg"], 0)
        self.assertEqual(founder_available(t0, first - timedelta(microseconds=1))["vested_deferred_mfrg"], 0)
        at_month13 = founder_available(t0, first)
        self.assertEqual(at_month13["vested_installments"], 1)
        self.assertEqual(at_month13["vested_deferred_mfrg"], MONTHLY_DEFERRED)
        self.assertEqual(at_month13["total_available_mfrg"], 15_625_000)

    def test_05_year2_7point5m_and_year3_full_15m(self):
        t0 = parse_utc("2026-10-28T00:00:00Z")
        at_year2 = founder_available(t0, add_calendar_months(t0, 24))
        self.assertEqual(at_year2["vested_installments"], 12)
        self.assertEqual(at_year2["vested_deferred_mfrg"], 7_500_000)
        self.assertEqual(at_year2["total_available_mfrg"], 22_500_000)
        at_year3 = founder_available(t0, add_calendar_months(t0, 36))
        self.assertEqual(at_year3["vested_installments"], 24)
        self.assertEqual(at_year3["vested_deferred_mfrg"], 15_000_000)
        self.assertEqual(at_year3["total_available_mfrg"], 30_000_000)
        self.assertEqual(founder_available(t0, add_calendar_months(t0, 42)), at_year3)

    def test_06_before_launch_zero_and_hypothetical_only(self):
        t0 = parse_utc("2026-10-28T00:00:00Z")
        self.assertEqual(founder_available(t0, t0 - timedelta(seconds=1))["total_available_mfrg"], 0)
        report = build_report(
            self.plan, self.status, self.registry,
            hypothetical_launch="2026-10-28T00:00:00Z", as_of="2028-10-28T00:00:00Z"
        )
        self.assertEqual(report["simulation"]["founder_if_validly_issued_and_funded"]["total_available_mfrg"], 22_500_000)
        self.assertTrue(report["simulation"]["hypothetical_only"])
        self.assertFalse(report["simulation"]["actual_launch_or_issuance_confirmed"])
        self.assertFalse(report["sale_or_issuance_authorized"])

    def test_07_calendar_month_clamping_without_drift(self):
        t0 = parse_utc("2027-01-31T23:45:00Z")
        self.assertEqual(add_calendar_months(t0, 13).isoformat(), "2028-02-29T23:45:00+00:00")
        self.assertEqual(add_calendar_months(t0, 14).isoformat(), "2028-03-31T23:45:00+00:00")
        self.assertEqual(add_calendar_months(t0, 25).isoformat(), "2029-02-28T23:45:00+00:00")
        self.assertEqual(add_calendar_months(t0, 26).isoformat(), "2029-03-31T23:45:00+00:00")
        self.assertEqual(len(set(x["release_utc"] for x in founder_vesting_schedule(t0))), 24)

    def test_08_utc_required_to_avoid_local_dst_ambiguity(self):
        for input_value in ("2026-10-28T00:00:00", "2026-10-28T00:00:00-04:00", "yesterday", ""):
            with self.subTest(value=input_value), self.assertRaises(PreflightError):
                parse_utc(input_value)
        self.assertEqual(parse_utc("2026-10-28T00:00:00+00:00"),
                         parse_utc("2026-10-28T00:00:00Z"))

    def test_09_missing_launch_cannot_be_simulated(self):
        with self.assertRaises(PreflightError):
            build_report(self.plan, self.status, self.registry, as_of="2027-10-28T00:00:00Z")

    def test_10_block_wallet_and_mint_claims_in_registry(self):
        for field, value in (("network_mint_address", "11111111111111111111111111111111"),
                             ("launch_utc", "2026-10-28T00:00:00Z"),
                             ("mode", "PRODUCTION")):
            modified = copy.deepcopy(self.registry)
            modified[field] = value
            with self.subTest(field=field), self.assertRaises(PreflightError):
                assess_plan(self.plan, self.status, modified)
        modified = copy.deepcopy(self.registry)
        modified["accounts"][0]["token_account"] = "11111111111111111111111111111111"
        with self.assertRaises(PreflightError):
            assess_plan(self.plan, self.status, modified)

    def test_11_no_false_positive_treasury_balances_or_permissions(self):
        for field in self.registry["verification"]:
            changed = copy.deepcopy(self.registry)
            changed["verification"][field] = True
            with self.subTest(field=field), self.assertRaises(PreflightError):
                assess_plan(self.plan, self.status, changed)
        for field, value in (("funded_verified", True), ("verified_balance_atomic", "1000")):
            changed = copy.deepcopy(self.registry)
            changed["accounts"][1][field] = value
            with self.subTest(field=field), self.assertRaises(PreflightError):
                assess_plan(self.plan, self.status, changed)

    def test_12_duplicate_account_or_supply_tampering_fails(self):
        changed = copy.deepcopy(self.registry)
        changed["accounts"][0]["id"] = changed["accounts"][1]["id"]
        with self.assertRaises(PreflightError):
            assess_plan(self.plan, self.status, changed)
        changed = copy.deepcopy(self.registry)
        changed["accounts"][0]["allocation_atomic"] = "50000000000000"
        with self.assertRaises(PreflightError):
            assess_plan(self.plan, self.status, changed)
        changed = copy.deepcopy(self.plan)
        changed["allocations"][0]["release_ceiling_by_period_mfrg"]["year_1"] += 1
        with self.assertRaises(PreflightError):
            assess_plan(changed, self.status, self.registry)

    def test_13_founder_label_and_lock_changes_fail(self):
        for key, value in (("monthly_vesting_first_month", 12),
                           ("monthly_vesting_last_month", 48),
                           ("monthly_tokens_ui", "600000"),
                           ("beneficial_owner", "independent employees")):
            changed = copy.deepcopy(self.plan)
            changed["founder"][key] = value
            with self.subTest(field=key), self.assertRaises(PreflightError):
                assess_plan(changed, self.status, self.registry)

    def test_14_5m_pilot_and_disabled_public_sale_cannot_change(self):
        changed = copy.deepcopy(self.plan)
        changed["fundraising"]["pilot_inventory_ui"] = "50000000"
        with self.assertRaises(PreflightError):
            assess_plan(changed, self.status, self.registry)
        for key in ("sale_enabled", "quotes_enabled", "payments_enabled", "fulfillment_enabled"):
            changed_status = copy.deepcopy(self.status)
            changed_status[key] = True
            with self.subTest(field=key), self.assertRaises(PreflightError):
                assess_plan(self.plan, changed_status, self.registry)

    def test_15_production_token_mint_not_silently_enabled(self):
        changed = copy.deepcopy(self.plan)
        changed["network_mint_address"] = "11111111111111111111111111111111"
        with self.assertRaises(PreflightError):
            assess_plan(changed, self.status, self.registry)
        changed = copy.deepcopy(self.plan)
        changed["is_issuance_authorized"] = True
        with self.assertRaises(PreflightError):
            assess_plan(changed, self.status, self.registry)


if __name__ == "__main__":
    unittest.main(verbosity=2)
