#!/usr/bin/env python3
import pathlib
import unittest
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":self.links.extend(v for k,v in attrs if k=="href")
class Checks(unittest.TestCase):
    def test_status_and_allocation(self):
        page=(ROOT/"docs/project-status.html").read_text()
        # Current 50M policy and release gates, not the superseded 500M draft.
        for expected in ("50,000,000 mFRG", "5M presale (10%)",
                         "5M future liquidity (10%)",
                         "40M combined staking/collateral/ecosystem (80%)",
                         "$0.12", "90% project / 10% founders",
                         "Development / prelaunch", "No authorized mFRG sale",
                         "Future mining-security proposals",
                         "independently reviewed hard fork"):
            self.assertIn(expected, page)
        self.assertNotIn("500,000,000 mFRG", page)
    def test_internal_links(self):
        p=Parser();p.feed((ROOT/"docs/project-status.html").read_text())
        for href in p.links:
            if href.startswith(("https://","#","mailto:")):continue
            self.assertTrue((ROOT/"docs"/href.split("#")[0]).exists(),href)
    def test_site_navigation(self):
        for f in ("docs/index.html","docs/miniforge-sale.html","docs/miniforge-tokenomics.html"):
            self.assertIn("project-status.html",(ROOT/f).read_text(),f)
    def test_merged_mining_proposals_remain_research_only(self):
        for name in ("docs/index.html", "docs/mining.html",
                     "docs/current-mainnet.html", "docs/pool-network.html",
                     "docs/project-status.html"):
            page = (ROOT/name).read_text()
            self.assertIn("Tari", page, name)
            self.assertIn("Monero", page, name)
            self.assertIn("future", page.lower(), name)
        self.assertIn("consensus", (ROOT/"docs/mining.html").read_text())

    def test_repo_docs(self):
        for f in ("README.md","ROADMAP.md","docs/index.md"):
            self.assertIn("project-status.html",(ROOT/f).read_text())
if __name__=="__main__":unittest.main()
