"""Public miniFORGE static site safety tests for the superseding 50M proposal.

The old sandbox backend still holds an ARCHIVED 500M economic model and is
NOT a live backend for the current static planning page. Its payments remain
unconditionally disabled. Never resurrect deprecated checkout controls just
to satisfy obsolete 2026-10-28 UI assertions.
"""
import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "apps" / "sale"))
from wsgi import STATUS
from sale_core import PRODUCTION_PAYMENT_COLLECTION_ENABLED


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.inputs = []
        self.buttons = []
        self.sources = []
        self.links = []
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"])
        if tag == "input":
            self.inputs.append(a)
        if tag == "button":
            self.buttons.append(a)
        if tag == "script":
            self.scripts.append(a)
        if a.get("src"):
            self.sources.append(a["src"])
        if a.get("href"):
            self.links.append(a["href"])


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (DOCS / "miniforge-sale.html").read_text(encoding="utf-8")
        cls.home = (DOCS / "index.html").read_text(encoding="utf-8")
        cls.status = json.loads((DOCS / "sale-status.json").read_text(encoding="utf-8"))
        cls.tags = Tags()
        cls.tags.feed(cls.html)

    def test_01_static_page_has_unique_element_ids(self):
        self.assertEqual(len(self.tags.ids), len(set(self.tags.ids)))
        self.assertIn('href="project-status.html"', self.html)

    def test_02_no_checkout_wallet_signing_or_executable_sale(self):
        # The superseding planning page intentionally has NO wallet/checkout UI.
        self.assertEqual(self.tags.inputs, [])
        self.assertEqual(self.tags.buttons, [])
        self.assertEqual(self.tags.scripts, [])
        for term in ("sale.js", "token-amount", "quote-button",
                     "connect-wallet", "signTransaction", "sendTransaction",
                     "sendAndConfirmTransaction", "wallet-adapter",
                     "solana:", "secretKey", "localStorage.setItem"):
            self.assertNotIn(term, self.html)
        for key in ("sale_enabled", "payments_enabled",
                    "quotes_enabled", "fulfillment_enabled"):
            self.assertIs(self.status[key], False)
        self.assertIsNone(self.status["token_mainnet_mint"])
        self.assertIsNone(self.status["sale_price_usdc"])

    def test_03_current_public_50m_allocation_exact(self):
        s = self.status
        self.assertEqual(s["supply_total_mfrg"], 50_000_000)
        self.assertEqual(s["sale_treasury_mfrg"], 5_000_000)
        self.assertEqual(s["initial_pilot_mfrg"], 5_000_000)
        self.assertEqual(s["future_liquidity_reserve_mfrg"], 5_000_000)
        self.assertEqual(s["future_distribution_reserve_mfrg"], 40_000_000)
        self.assertEqual(s["allocation_mfrg"], {
            "initial_presale": 5_000_000,
            "future_liquidity": 5_000_000,
            "combined_ecosystem_staking_collateral": 40_000_000,
        })
        self.assertEqual(sum(s["allocation_mfrg"].values()), 50_000_000)

    def test_04_public_content_explicitly_proposed_and_unavailable(self):
        for msg in ("No sale is authorized", "50,000,000 total supply",
                    "5,000,000 mFRG", "$0.12", "90% project",
                    "5% founder immediate", "six months", "Do not transfer SOL",
                    "No mint, sale, bridge", "1 FRG : 1 mFRG"):
            self.assertIn(msg, self.html)
        self.assertIn("50M miniFORGE", self.home)
        self.assertNotIn("500M mFRG", self.html + self.home)
        self.assertNotIn("Buy mFRG now", self.home)

    def test_05_static_assets_and_links_resolve(self):
        for item in self.tags.sources + self.tags.links:
            if item.startswith(("#", "http://", "https://", "mailto:")):
                continue
            candidate = DOCS / item.split("?")[0].split("#")[0]
            self.assertTrue(candidate.is_file(), f"Missing file: {item}")

    def test_06_no_unauthorized_payment_address_or_transaction_url(self):
        for phrase in ("solana:", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                       "9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw"):
            self.assertNotIn(phrase, self.html)

    def test_07_mobile_and_accessibility_indicators(self):
        self.assertIn('name="viewport"', self.html)
        self.assertIn('aria-label="Navigation"', self.html)
        self.assertIn('role="img"', self.html)
        self.assertIn("<figcaption>", self.html)
        self.assertIn("<table>", self.html)
        self.assertIn('<strong>No sale is authorized', self.html)

    def test_08_legacy_sandbox_never_authorizes_public_sale(self):
        # Legacy 500M offline sandbox economics are superseded and incompatible
        # with the current 50M *static-only* policy. The backend is intentionally
        # not referenced by the static page. Keep it fail-closed pending a
        # separately reviewed 50M rewrite rather than misrepresenting it.
        self.assertIs(PRODUCTION_PAYMENT_COLLECTION_ENABLED, False)
        for key in ("sale_enabled", "payments_enabled",
                    "quotes_enabled", "fulfillment_enabled"):
            self.assertIs(STATUS[key], False)
        self.assertIsNone(STATUS["token_mainnet_mint"])
        self.assertIsNone(STATUS["sale_price_usdc"])
        self.assertNotEqual(STATUS["supply_total_mfrg"],
                            self.status["supply_total_mfrg"])
        self.assertEqual(self.status["network"], "solana-mainnet-beta")


if __name__ == "__main__":
    unittest.main(verbosity=2)
