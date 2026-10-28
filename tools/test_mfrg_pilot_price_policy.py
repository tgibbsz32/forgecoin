#!/usr/bin/env python3
import pathlib,unittest,re
BASE=pathlib.Path(__file__).resolve().parents[1]
class PricePolicyTests(unittest.TestCase):
 def test_exact_five_rounds_and_gross(self):
  text=(BASE/"docs/MFRG_PILOT_PRICE_AND_USE_OF_PROCEEDS.md").read_text()
  for price,gross in [("0.08","80,000"),("0.10","100,000"),("0.12","120,000"),("0.14","140,000"),("0.16","160,000")]:
   self.assertRegex(text,re.escape("$"+price)+r"\s*\|\s*\$"+gross)
  self.assertIn("**$600,000**",text)
  self.assertIn("**$120,000 (20%) founder proceeds**",text)
 def test_legal_release_block(self):
  text=(BASE/"docs/MFRG_PILOT_PRELIMINARY_US_LEGAL_REVIEW_2026-10-28.md").read_text()
  for word in ("LEGAL_RELEASE_APPROVED=false","PUBLIC_OFFERING_AUTHORIZED=false","PAYMENTS_ENABLED=false","Howey","FinCEN","South Carolina"):
   self.assertIn(word,text)
 def test_sale_pages_include_hold(self):
  for file in ("docs/miniforge-sale.html","docs/miniforge-tokenomics.html","docs/project-status.html"):
   text=(BASE/file).read_text()
   self.assertIn("MFRG_PILOT_PRELIMINARY_US_LEGAL_REVIEW_2026-10-28.md",text)
   self.assertIn("NO PUBLIC OFFER AUTHORIZED",text)
 def test_no_checkout_activation(self):
  text=(BASE/"apps/desktop/config/miniFORGE.mainnet.plan.json").read_text()
  self.assertIn('"checkout_enabled": false',text)
  self.assertIn('"is_sale_authorized": false',text)
 def test_policy_does_not_change_total(self):
  text=(BASE/"docs/MFRG_PILOT_PRICE_AND_USE_OF_PROCEEDS.md").read_text()
  self.assertIn("500,000,000",text)
  self.assertIn("nine mutually exclusive",text)
if __name__=="__main__":unittest.main()
