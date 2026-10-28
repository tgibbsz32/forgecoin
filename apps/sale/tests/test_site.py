"""Offline website policy and sale-lock tests. No on-chain connections."""
import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "apps" / "sale"))
from wsgi import STATUS, ALLOCATION

class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.inputs = []
        self.buttons = []
        self.sources = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"])
        if tag == "input":
            self.inputs.append(a)
        if tag == "button":
            self.buttons.append(a)
        if a.get("src"):
            self.sources.append(a["src"])
        if a.get("href"):
            self.links.append(a["href"])

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (DOCS / "miniforge-sale.html").read_text(encoding="utf-8")
        cls.home = (DOCS / "index.html").read_text(encoding="utf-8")
        cls.js = (DOCS / "sale.js").read_text(encoding="utf-8")
        cls.css = (DOCS / "sale.css").read_text(encoding="utf-8")
        cls.status = json.loads((DOCS / "sale-status.json").read_text(encoding="utf-8"))
        cls.tags = Tags()
        cls.tags.feed(cls.html)

    def test_01_no_duplicate_element_ids(self):
        self.assertEqual(len(self.tags.ids), len(set(self.tags.ids)))
        for name in ("token-amount", "quote-button", "connect-wallet",
                     "wallet-state", "sale-status", "mint-address",
                     "token-price", "checkout-state"):
            self.assertIn(name, self.tags.ids)

    def test_02_disabled_checkout_and_no_signing(self):
        amount = next(a for a in self.tags.inputs if a.get("id") == "token-amount")
        button = next(a for a in self.tags.buttons if a.get("id") == "quote-button")
        self.assertIn("disabled", amount)
        self.assertIn("disabled", button)
        self.assertIn("const CHECKOUT_LOCKED = true", self.js)
        self.assertIn("quoteButton.disabled = true", self.js)
        for phrase in ("signTransaction", "sendTransaction", "sendAndConfirmTransaction",
                       "signAllTransactions", "secretKey", "privateKey",
                       "seedPhrase", "localStorage.setItem("):
            self.assertNotIn(phrase, self.js)

    def test_03_nine_allocation_status(self):
        s = self.status
        for key in ("sale_enabled", "payments_enabled", "quotes_enabled", "fulfillment_enabled"):
            self.assertIs(s[key], False)
        self.assertIsNone(s["token_mainnet_mint"])
        self.assertIsNone(s["sale_price_usdc"])
        self.assertEqual(s["supply_total_mfrg"], 500_000_000)
        self.assertEqual(s["sale_treasury_mfrg"], 50_000_000)
        self.assertEqual(s["initial_pilot_mfrg"], 5_000_000)
        self.assertEqual(s["future_liquidity_reserve_mfrg"], 60_000_000)
        self.assertEqual(s["future_distribution_reserve_mfrg"], 390_000_000)
        self.assertEqual(sum(s["allocation_mfrg"].values()), 500_000_000)
        self.assertEqual(s["founder_beneficial_total_mfrg"], 30_000_000)

    def test_04_public_content_discloses_proposed_status_and_founder(self):
        for msg in ("Sale not open", "500,000,000", "50,000,000",
                    "60,000,000", "30,000,000", "native FRG",
                    "Do not send SOL, USDC or FRG"):
            self.assertIn(msg, self.html)
        self.assertIn("500M mFRG", self.home)
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
        self.assertIn("@media(max-width:490px)", self.css)
        self.assertIn("prefers-reduced-motion", self.css)
        self.assertIn('aria-label="Sale availability"', self.html)
        self.assertIn('aria-describedby="disabled-note"', self.html)
        self.assertIn('role="status"', self.html)

    def test_08_static_status_and_read_only_backend_agree(self):
        for key in ("network", "sale_enabled", "payments_enabled",
                    "quotes_enabled", "fulfillment_enabled", "sale_price_usdc",
                    "token_mainnet_mint", "sale_treasury_mfrg",
                    "initial_pilot_mfrg", "future_liquidity_reserve_mfrg",
                    "future_distribution_reserve_mfrg", "supply_total_mfrg",
                    "founder_beneficial_total_mfrg"):
            self.assertEqual(self.status[key], STATUS[key], key)
        self.assertEqual(self.status["allocation_mfrg"], STATUS["allocation_mfrg"])
        self.assertEqual(ALLOCATION["pilot_sale_cap_tokens"], 5_000_000)
        self.assertIs(ALLOCATION["sale_contract_deployed"], False)

if __name__ == "__main__":
    unittest.main(verbosity=2)
