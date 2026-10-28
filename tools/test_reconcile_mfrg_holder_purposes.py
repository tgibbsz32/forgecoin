#!/usr/bin/env python3
"""Synthetic no-network Step 18 assertions."""
import copy
import unittest
from reconcile_mfrg_holder_purposes import reconcile, ReconciliationError, BUDGETS, UNIT

MINT = "A" * 43
SIGNATURE = "B" * 88

def example():
    return {
        "schema_version": 1,
        "network": "solana-mainnet-beta",
        "token_program": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        "decimals": 6,
        "mint": MINT,
        "initialization_signature": SIGNATURE,
        "mint_supply_atomic": 2 * UNIT,
        "accounts": [
            {"token_account": "C" * 43, "amount_atomic": UNIT, "purpose": "operations",
             "owner_attestation_verified": True, "governance_authorization_verified": True,
             "beneficial_owner_verified": True},
            {"token_account": "D" * 43, "amount_atomic": UNIT, "purpose": "unassigned"},
        ],
    }

class PurposeTests(unittest.TestCase):
    def test_baseline_is_not_cryptographic_proof(self):
        result = reconcile(example())
        self.assertFalse(result["sale_authorized"])
        self.assertFalse(result["claims_cryptographically_verified_by_this_script"])
        self.assertEqual(result["unassigned_atomic"], UNIT)

    def test_budgets_total(self):
        self.assertEqual(sum(BUDGETS.values()), 500_000_000)

    def assert_blocked(self, mutate):
        doc = example()
        mutate(doc)
        with self.assertRaises((ReconciliationError, TypeError)):
            reconcile(doc)

    def test_duplicate_account(self):
        self.assert_blocked(lambda d: d["accounts"].append(copy.deepcopy(d["accounts"][0])))

    def test_supply_mismatch(self):
        self.assert_blocked(lambda d: d.update(mint_supply_atomic=3 * UNIT))

    def test_unattested_owner(self):
        self.assert_blocked(lambda d: d["accounts"][0].update(owner_attestation_verified=False))

    def test_unattested_governance(self):
        self.assert_blocked(lambda d: d["accounts"][0].update(governance_authorization_verified=False))

    def test_unattested_beneficial_owner(self):
        self.assert_blocked(lambda d: d["accounts"][0].update(beneficial_owner_verified=False))

    def test_unknown_purpose(self):
        self.assert_blocked(lambda d: d["accounts"][0].update(purpose="secret_treasury"))

    def test_devnet_mint(self):
        self.assert_blocked(lambda d: d.update(mint="9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw"))

    def test_wrong_chain(self):
        self.assert_blocked(lambda d: d.update(network="devnet"))

    def test_wrong_program(self):
        self.assert_blocked(lambda d: d.update(token_program="bad"))

    def test_boolean_amount(self):
        self.assert_blocked(lambda d: d["accounts"][0].update(amount_atomic=True))

    def test_overallocation(self):
        self.assert_blocked(lambda d: (d["accounts"][0].update(amount_atomic=101_000_000 * UNIT),
                                      d.update(mint_supply_atomic=101_000_001 * UNIT)))

    def test_excess_supply(self):
        self.assert_blocked(lambda d: (d["accounts"][1].update(amount_atomic=500_000_000 * UNIT),
                                      d.update(mint_supply_atomic=500_000_001 * UNIT)))

    def test_missing_signature(self):
        self.assert_blocked(lambda d: d.update(initialization_signature=""))

    def test_missing_inventory(self):
        self.assert_blocked(lambda d: d.update(accounts=[]))

if __name__ == "__main__":
    unittest.main()
