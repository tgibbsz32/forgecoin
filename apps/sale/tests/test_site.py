"""Static sale-page acceptance: source and self-contained assets (no network)."""
from pathlib import Path
from html.parser import HTMLParser
import json, re, unittest

ROOT=Path(__file__).resolve().parents[3]
DOCS=ROOT/"docs"
class Tags(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.inputs=[];self.buttons=[];self.srcs=[];self.refs=[];self.all=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.all.append((tag,a))
        if a.get("id"):self.ids.append(a["id"])
        if tag=="input":self.inputs.append(a)
        if tag=="button":self.buttons.append(a)
        if a.get("src"):self.srcs.append(a["src"])
        if a.get("href"):self.refs.append(a["href"])
class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(DOCS/"miniforge-sale.html").read_text(encoding="utf-8")
        cls.home=(DOCS/"index.html").read_text(encoding="utf-8")
        cls.js=(DOCS/"sale.js").read_text(encoding="utf-8")
        cls.css=(DOCS/"sale.css").read_text(encoding="utf-8")
        cls.status=json.loads((DOCS/"sale-status.json").read_text(encoding="utf-8"))
        cls.parser=Tags();cls.parser.feed(cls.html)
    def test_01_html_controls_are_unique_and_identified(self):
        self.assertEqual(len(self.parser.ids),len(set(self.parser.ids)))
        for ident in ("token-amount","quote-button","connect-wallet","wallet-state",
                      "sale-status","mint-address","token-price","checkout"):
            self.assertIn(ident,self.parser.ids)
    def test_02_all_payment_controls_disabled_in_html(self):
        self.assertIn("disabled",next(x for x in self.parser.inputs if x["id"]=="token-amount"))
        self.assertIn("disabled",next(x for x in self.parser.buttons if x["id"]=="quote-button"))
        self.assertNotIn("disabled",next(x for x in self.parser.buttons if x["id"]=="connect-wallet"))
    def test_03_sale_status_hard_paused_exact_allocations(self):
        st=self.status
        self.assertEqual(st["schema"],"miniforge-sale-status-v1")
        self.assertFalse(st["sale_enabled"])
        self.assertFalse(st["payments_enabled"])
        self.assertFalse(st["quotes_enabled"])
        self.assertFalse(st["fulfillment_enabled"])
        self.assertIsNone(st["token_mainnet_mint"])
        self.assertIsNone(st["sale_price_usdc"])
        self.assertEqual([st["sale_treasury_mfrg"],st["future_liquidity_reserve_mfrg"],
                          st["future_distribution_reserve_mfrg"]],[5000000,5000000,40000000])
    def test_04_visible_site_never_implies_open_sale(self):
        for msg in ("Sale not open","not yet issued on Solana mainnet",
                    "Do not send SOL, USDC or FRG","No offer","No guaranteed"):
            self.assertIn(msg,self.html)
    def test_05_no_dangerous_payment_or_private_key_code(self):
        for code in ("signTransaction","sendTransaction","sendAndConfirmTransaction",
                     "signAllTransactions","signMessage","secretKey","privateKey",
                     "seedPhrase","document.cookie","localStorage.setItem("):
            self.assertNotIn(code,self.js)
        self.assertIn("CHECKOUT_LOCKED = true",self.js)
        self.assertIn("quoteButton.disabled = true",self.js)
    def test_06_reflects_exact_allocation_and_distinct_frG_mfrg(self):
        for value in ("50,000,000","5,000,000","40,000,000",
                      "native FRG","wFRG","Solana"):
            self.assertIn(value,self.html)
    def test_07_website_assets_and_internal_links_exist(self):
        for item in self.parser.srcs + self.parser.refs:
            if item.startswith(("#","http://","https://","mailto:")):continue
            path=(DOCS/item.split("#")[0].split("?")[0])
            self.assertTrue(path.is_file(),f"Missing asset or internal link: {item}")
    def test_08_home_page_links_to_planned_sale_not_live_buy_now(self):
        self.assertIn('href="miniforge-sale.html"',self.home)
        self.assertIn("mFRG Sale (planned)",self.home)
        self.assertNotIn("Buy mFRG now",self.home)
    def test_09_no_backend_endpoint_or_real_payment_recipient_in_html(self):
        self.assertNotIn("solana:",self.html)
        self.assertNotIn("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",self.html)
        self.assertNotIn("9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw",self.html)
    def test_10_css_mobile_layout_and_accessibility(self):
        self.assertIn("@media(max-width:490px)",self.css)
        self.assertIn("prefers-reduced-motion",self.css)
        self.assertIn('aria-label="Sale availability"',self.html)
        self.assertIn('aria-describedby="disabled-note"',self.html)
        self.assertIn('role="status"',self.html)
    def test_11_site_data_and_wsgi_inventory_match(self):
        import sys
        sys.path.insert(0,str(ROOT/"apps"/"sale"))
        from wsgi import STATUS
        for key in ("network","sale_enabled","payments_enabled","sale_price_usdc",
                    "token_mainnet_mint","sale_treasury_mfrg",
                    "future_liquidity_reserve_mfrg","future_distribution_reserve_mfrg"):
            self.assertEqual(self.status[key],STATUS[key])
if __name__=="__main__":
    unittest.main(verbosity=2)
