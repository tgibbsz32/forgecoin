#!/usr/bin/env python3
"""Superseding 50M mFRG informational-policy safeguards; NO sale execution.

The historical 500M sandbox backend and its tests are intentionally NOT a
current public-sale representation. Production remains closed regardless of
sandbox terms. No RPC, wallet, mint, funds or private data involved here.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class CurrentProposedMfrgPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status = json.loads((DOCS / "sale-status.json").read_text(encoding="utf-8"))
        cls.policy = (DOCS / "MFRG_50M_CITY_TOKENOMICS.md").read_text(encoding="utf-8")
        cls.sale_html = (DOCS / "miniforge-sale.html").read_text(encoding="utf-8")
        cls.home = (DOCS / "index.html").read_text(encoding="utf-8")

    def test_50m_supply_and_nonoverlapping_reserves(self):
        self.assertEqual(self.status["supply_total_mfrg"], 50_000_000)
        self.assertEqual(self.status["sale_treasury_mfrg"], 5_000_000)
        self.assertEqual(self.status["future_liquidity_reserve_mfrg"], 5_000_000)
        self.assertEqual(self.status["future_distribution_reserve_mfrg"], 40_000_000)
        self.assertEqual(self.status["allocation_mfrg"], {
            "initial_presale": 5_000_000,
            "future_liquidity": 5_000_000,
            "combined_ecosystem_staking_collateral": 40_000_000,
        })
        self.assertEqual(sum(self.status["allocation_mfrg"].values()), 50_000_000)
        self.assertLess(50_000_000 * 10**6, 2**64)

    def test_no_runtime_sale_mint_quotes_or_wallet_signing(self):
        for key in ("sale_enabled", "payments_enabled", "quotes_enabled",
                    "fulfillment_enabled"):
            self.assertIs(self.status[key], False)
        for key in ("token_mainnet_mint", "sale_price_usdc",
                    "sale_start", "sale_end"):
            self.assertIsNone(self.status[key])
        for forbidden in ("sale.js", "connect-wallet", "quote-button",
                          "signTransaction", "sendTransaction", "solana:"):
            self.assertNotIn(forbidden, self.sale_html)
        self.assertIn("No sale is authorized", self.sale_html)
        self.assertIn("Do not transfer SOL", self.sale_html)

    def test_project_first_governance_then_proposed_bridge_and_sale(self):
        self.assertIn("50,000,000 mFRG", self.policy)
        self.assertIn("5,000,000", self.policy)
        self.assertIn("40,000,000", self.policy)
        self.assertIn("$0.12", self.policy)
        self.assertIn("90% project / 10% founders", self.policy)
        self.assertIn("six months", self.policy)
        self.assertIn("1 FRG : 1 mFRG", self.policy)
        self.assertIn("No checkout, payment address", self.policy)
        self.assertIn("after native FRG release and governance adoption", self.policy)
        self.assertNotIn("500M mFRG", self.home)
        self.assertNotIn("Buy mFRG now", self.home)

    def test_legacy_offline_sandbox_not_mistaken_for_50m_public_site(self):
        # Source-only historical sandbox may still use 500M figures but is
        # locked at runtime. If a future rewrite adds a real sale backend,
        # make new audited tests instead of loosening this guard.
        from sys import path
        path.insert(0, str(ROOT / "apps" / "sale"))
        from sale_core import PRODUCTION_PAYMENT_COLLECTION_ENABLED
        from wsgi import STATUS
        self.assertIs(PRODUCTION_PAYMENT_COLLECTION_ENABLED, False)
        for key in ("sale_enabled", "quotes_enabled",
                    "payments_enabled", "fulfillment_enabled"):
            self.assertIs(STATUS[key], False)
        self.assertIsNone(STATUS["token_mainnet_mint"])
        self.assertNotEqual(STATUS["supply_total_mfrg"],
                            self.status["supply_total_mfrg"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
