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
        for expected in ("500,000,000","50,000,000","100,000,000","85,000,000","60,000,000","65,000,000","15,000,000","10,000,000","not yet been deployed","same beneficial owner","not guaranteed"):
            self.assertIn(expected,page)
        self.assertIn("No live mint address",page)
    def test_internal_links(self):
        p=Parser();p.feed((ROOT/"docs/project-status.html").read_text())
        for href in p.links:
            if href.startswith(("https://","#","mailto:")):continue
            self.assertTrue((ROOT/"docs"/href.split("#")[0]).exists(),href)
    def test_site_navigation(self):
        for f in ("docs/index.html","docs/miniforge-sale.html","docs/miniforge-tokenomics.html"):
            self.assertIn("project-status.html",(ROOT/f).read_text(),f)
    def test_repo_docs(self):
        for f in ("README.md","ROADMAP.md","docs/index.md"):
            self.assertIn("project-status.html",(ROOT/f).read_text())
if __name__=="__main__":unittest.main()
