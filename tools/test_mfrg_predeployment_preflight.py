#!/usr/bin/env python3
import copy
import json
import pathlib
import unittest
from mfrg_predeployment_preflight import assess,PreflightError
PLAN=pathlib.Path(__file__).resolve().parents[1]/"apps/desktop/config/miniFORGE.mainnet.plan.json"
def fixture():return json.loads(PLAN.read_text())
class Tests(unittest.TestCase):
 def test_repo_plan_consistent_but_not_authorized(self):
  out=assess(fixture())
  self.assertEqual(out["allocation_categories"],9)
  self.assertEqual(out["planned_total_atomic"],500_000_000_000_000)
  self.assertFalse(out["production_deployment_authorized"])
 def blocked(self,action):
  value=fixture();action(value)
  with self.assertRaises(PreflightError):assess(value)
 def test_oversupply(self):self.blocked(lambda p:p.update(target_supply_atomic="500000000000001"))
 def test_duplicate_category(self):self.blocked(lambda p:p["allocations"][1].update(id="fundraising"))
 def test_overallocated_tokens(self):self.blocked(lambda p:p["allocations"][0].update(tokens_ui="50000001"))
 def test_underallocated_atomic(self):self.blocked(lambda p:p["allocations"][0].update(amount_atomic="49999999999999"))
 def test_unbalanced_schedule(self):self.blocked(lambda p:p["allocations"][0]["release_ceiling_by_period_mfrg"].update(year_1=1))
 def test_period_total_disagreement(self):self.blocked(lambda p:p["release_schedule_total_by_period_mfrg"].update(year_1=1))
 def test_wrong_decimals(self):self.blocked(lambda p:p.update(decimals=9))
 def test_wrong_program(self):self.blocked(lambda p:p.update(token_program="Token2022"))
 def test_live_checkout(self):self.blocked(lambda p:p["fundraising"].update(checkout_enabled=True))
 def test_live_mint(self):self.blocked(lambda p:p.update(network_mint_address="1"*32))
 def test_issuance_enabled(self):self.blocked(lambda p:p.update(is_issuance_authorized=True))
 def test_fake_account(self):self.blocked(lambda p:p["allocations"][0].update(account_address="1"*32))
 def test_short_founder_schedule(self):self.blocked(lambda p:p["founder"].update(monthly_vesting_last_month=35))
 def test_changed_pilot(self):self.blocked(lambda p:p["fundraising"].update(pilot_inventory_ui="50000000"))
 def test_boolean_decimals(self):self.blocked(lambda p:p.update(decimals=True))
 def test_missing_category(self):self.blocked(lambda p:p["allocations"].pop())
if __name__=="__main__":unittest.main()
