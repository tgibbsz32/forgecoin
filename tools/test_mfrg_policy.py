#!/usr/bin/env python3
"""Offline, read-only consistency checks for mFRG lifetime policy.

No RPC, key material, minting, sale execution, token transfer, or external packages.
Run: python3 tools/test_mfrg_policy.py
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "apps/desktop/config/miniFORGE.mainnet.plan.json"
STATUS = ROOT / "docs/sale-status.json"
SALE_JS = ROOT / "docs/sale.js"
SALE_HTML = ROOT / "docs/miniforge-sale.html"
PUBLIC_POLICY = ROOT / "docs/MFRG_LIFETIME_TOKENOMICS_500M.md"
WALLET = ROOT / "apps/desktop/SolanaWallet.cs"

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
    "year_1": 74_000_000,
    "years_2_3": 95_000_000,
    "years_4_10": 117_000_000,
    "years_11_20": 113_000_000,
    "years_21_30": 101_000_000,
}
DECIMALS = 6
ATOMIC = 10 ** DECIMALS
TOTAL = 500_000_000


class MfrgPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN.read_text(encoding="utf-8-sig"))
        cls.status = json.loads(STATUS.read_text(encoding="utf-8-sig"))
        cls.js = SALE_JS.read_text(encoding="utf-8")
        cls.sale_html = SALE_HTML.read_text(encoding="utf-8")
        cls.policy = PUBLIC_POLICY.read_text(encoding="utf-8")
        cls.wallet = WALLET.read_text(encoding="utf-8")

    def test_fixed_supply_and_atomic_amount(self):
        p = self.plan
        self.assertEqual(p["schema_version"], 2)
        self.assertEqual(p["configuration_type"], "NON_TRANSACTIONAL_PLANNING_DATA_ONLY")
        self.assertEqual(p["decimals"], DECIMALS)
        self.assertEqual(p["token_program"], "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
        self.assertEqual(int(p["target_supply_ui"]), TOTAL)
        self.assertEqual(int(p["target_supply_atomic"]), TOTAL * ATOMIC)
        self.assertLess(TOTAL * ATOMIC, 2 ** 64)

    def test_each_allocation_and_separate_account(self):
        allocations = self.plan["allocations"]
        self.assertEqual(len(allocations), 9)
        found = {a["id"]: a for a in allocations}
        self.assertEqual(set(found), set(EXPECTED))
        for name, value in EXPECTED.items():
            with self.subTest(allocation=name):
                a = found[name]
                self.assertEqual(int(a["tokens_ui"]), value)
                self.assertEqual(int(a["amount_atomic"]), value * ATOMIC)
                self.assertIsNone(a["account_address"])
                self.assertIsNone(a["custody_authority"])
        self.assertEqual(sum(int(a["tokens_ui"]) for a in allocations), TOTAL)
        self.assertEqual(sum(int(a["amount_atomic"]) for a in allocations), TOTAL * ATOMIC)

    def test_release_schedule_matches_allocation_budgets(self):
        found = {a["id"]: a for a in self.plan["allocations"]}
        for name, amount in EXPECTED.items():
            values = found[name]["release_ceiling_by_period_mfrg"]
            self.assertEqual(set(values), set(PERIODS))
            self.assertEqual(sum(values.values()), amount, name)
        for period, expected in PERIODS.items():
            self.assertEqual(
                sum(a["release_ceiling_by_period_mfrg"][period] for a in found.values()),
                expected,
                period,
            )
            self.assertEqual(
                self.plan["release_schedule_total_by_period_mfrg"][period], expected
            )
        self.assertEqual(sum(PERIODS.values()), TOTAL)

    def test_founder_beneficial_ownership_and_vesting(self):
        f = self.plan["founder"]
        self.assertEqual(int(f["total_tokens_ui"]), 30_000_000)
        self.assertEqual(f["immediate_id"], "founder_immediate")
        self.assertEqual(f["deferred_id"], "founder_deferred_team_label")
        self.assertEqual(f["monthly_vesting_first_month"], 13)
        self.assertEqual(f["monthly_vesting_last_month"], 36)
        self.assertEqual(int(f["monthly_tokens_ui"]), 625_000)
        self.assertEqual(int(f["monthly_amount_atomic"]), 625_000 * ATOMIC)
        self.assertEqual(625_000 * (36 - 13 + 1), EXPECTED["founder_deferred_team_label"])
        self.assertEqual(self.status["founder_beneficial_total_mfrg"], 30_000_000)

    def test_fundraising_pilot_and_followon_inventory(self):
        funding = self.plan["fundraising"]
        self.assertEqual(int(funding["total_inventory_ui"]), EXPECTED["fundraising"])
        self.assertEqual(
            sum(int(funding[name]) for name in (
                "pilot_inventory_ui", "additional_year_1_ui",
                "years_2_3_ui", "years_4_10_ui"
            )),
            EXPECTED["fundraising"],
        )
        self.assertEqual(int(funding["pilot_inventory_ui"]), 5_000_000)
        self.assertEqual(funding["approved_consideration_assets"], [])
        self.assertIsNone(funding["price"])
        self.assertIsNone(funding["sale_start"])
        self.assertIsNone(funding["sale_end"])
        self.assertIs(funding["checkout_enabled"], False)

    def test_staking_is_only_a_finite_proposal(self):
        stake = self.plan["staking_policy_design"]
        self.assertEqual(stake["status"], "PROPOSED_NOT_DEPLOYED")
        self.assertEqual(int(stake["reward_reserve_ui"]), 85_000_000)
        self.assertEqual(stake["lock_days"], [30, 90, 180, 365])
        self.assertEqual(stake["lock_reward_weights"], ["1.00", "1.10", "1.20", "1.40"])
        self.assertEqual(stake["claim_cadence_days"], 7)
        self.assertEqual(stake["withdrawal_cooldown_days_after_maturity"], 7)
        self.assertIs(stake["guaranteed_apy"], False)
        self.assertIs(stake["secures_frg_pow"], False)

    def test_public_status_reconciles_and_cannot_open_sale(self):
        s = self.status
        self.assertEqual(s["supply_total_mfrg"], TOTAL)
        self.assertEqual(s["sale_treasury_mfrg"], 50_000_000)
        self.assertEqual(s["initial_pilot_mfrg"], 5_000_000)
        self.assertEqual(s["future_liquidity_reserve_mfrg"], 60_000_000)
        self.assertEqual(s["future_distribution_reserve_mfrg"], 390_000_000)
        self.assertEqual(s["allocation_mfrg"], EXPECTED)
        for key in (
            "sale_enabled", "payments_enabled", "quotes_enabled", "fulfillment_enabled"
        ):
            self.assertIs(s[key], False, key)
        self.assertIsNone(s["token_mainnet_mint"])
        self.assertIsNone(s["sale_price_usdc"])

    def test_production_actions_remain_disabled(self):
        p = self.plan
        for key in (
            "is_issuance_authorized", "is_sale_authorized",
            "is_staking_authorized", "is_liquidity_authorized",
            "fixed_cap_enforced", "allocation_completed"
        ):
            self.assertIs(p[key], False, key)
        self.assertIsNone(p["network_mint_address"])
        self.assertIn("const CHECKOUT_LOCKED = true", self.js)
        self.assertIn('quoteButton.disabled = true', self.js)
        self.assertIn('amountInput.disabled = true', self.js)
        self.assertNotIn("sendTransaction(", self.js)

    def test_site_js_guard_and_required_ids(self):
        for key, value in (
            ("supply_total_mfrg", 500000000),
            ("sale_treasury_mfrg", 50000000),
            ("future_liquidity_reserve_mfrg", 60000000),
            ("future_distribution_reserve_mfrg", 390000000),
        ):
            self.assertIn(f"status.{key} !== {value}", self.js)
        ids = re.findall(r"\$\('([A-Za-z0-9-]+)'\)", self.js)
        self.assertTrue(ids)
        for name in ids:
            self.assertIn(f'id="{name}"', self.sale_html, name)

    def test_wallet_uses_separate_production_mint_gate(self):
        self.assertIn('"miniFORGE.mainnet.json"', self.wallet)
        self.assertNotIn('"miniFORGE.mainnet.plan.json"', self.wallet)
        self.assertIn('!Convert.ToBoolean(settings["productionReady"])', self.wallet)
        self.assertIn("Mainnet mint unconfigured", self.wallet)

    def test_public_policy_discloses_founder_and_tail(self):
        self.assertIn("500,000,000", self.policy)
        self.assertIn("30M total, 6%", self.policy)
        self.assertIn("625,000", self.policy)
        self.assertIn("months 13–36", self.policy)
        self.assertIn("0.20 FRG tail", self.policy)


if __name__ == "__main__":
    unittest.main(verbosity=2)
