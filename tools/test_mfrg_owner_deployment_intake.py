#!/usr/bin/env python3
"""Synthetic-only deployment intake checks; does not contact Solana."""
import copy
import unittest
from mfrg_owner_deployment_intake import validate, IntakeError, DEVNET_MINT

def sample():
    return {
      "version":1,"network":"solana-mainnet-beta",
      "mint":"11111111111111111111111111111111",
      "initialization_signature":"1"*64,
      "owner_statement_url":"https://example.org/owner-statement",
      "initialization_history_url":"https://history.example.org/transaction",
      "independent_source_urls":[
          "https://explorer-one.example.org/snapshot",
          "https://explorer-two.example.org/snapshot"]
    }

class IntakeTests(unittest.TestCase):
    def test_synthetic_valid_but_never_authenticated(self):
        r=validate(sample())
        self.assertFalse(r["owner_authorization_authenticated"])
        self.assertFalse(r["minting_authorized"])
    def blocked(self,mutate):
        obj=sample();mutate(obj)
        with self.assertRaises((IntakeError,ValueError)):
            validate(obj)
    def test_devnet_mint(self):self.blocked(lambda o:o.update(mint=DEVNET_MINT))
    def test_devnet_network(self):self.blocked(lambda o:o.update(network="devnet"))
    def test_invalid_base58(self):self.blocked(lambda o:o.update(mint="0"*32))
    def test_missing_signature(self):self.blocked(lambda o:o.update(initialization_signature=""))
    def test_non_https(self):self.blocked(lambda o:o.update(owner_statement_url="http://example.org"))
    def test_embedded_credentials(self):self.blocked(lambda o:o.update(owner_statement_url="https://alice:secret@example.org"))
    def test_duplicate_sources(self):self.blocked(lambda o:o["independent_source_urls"].__setitem__(1,o["independent_source_urls"][0]))
    def test_missing_source(self):self.blocked(lambda o:o.update(independent_source_urls=[]))
    def test_extra_field(self):self.blocked(lambda o:o.update(secret="do not collect"))
    def test_bool_version(self):self.blocked(lambda o:o.update(version=True))
    def test_localhost(self):self.blocked(lambda o:o.update(owner_statement_url="https://localhost/a"))
    def test_fragment(self):self.blocked(lambda o:o.update(initialization_history_url="https://history.example.org/a#token"))
if __name__=="__main__":unittest.main()
