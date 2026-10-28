#!/usr/bin/env python3
"""Non-transactional mFRG 500M deployment-plan audit.

Reads a planning JSON. Never invokes Solana RPC, creates keys, signs, or submits
transactions. A PASS is policy consistency, NEVER mainnet release approval.
"""
import argparse
import json
import pathlib
import sys

EXPECTED={
 "fundraising":50_000_000,"operations":100_000_000,
 "ecosystem":100_000_000,"staking":85_000_000,
 "liquidity":60_000_000,"engineering_security":65_000_000,
 "founder_immediate":15_000_000,"founder_deferred_team_label":15_000_000,
 "emergency":10_000_000,
}
PERIODS=("year_1","years_2_3","years_4_10","years_11_20","years_21_30")
PROGRAM="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOTAL=500_000_000
SCALE=1_000_000

class PreflightError(ValueError):pass
def require(value,reason):
    if not value:raise PreflightError(reason)
def positive_integer_string(value,reason):
    require(isinstance(value,str) and value.isdecimal() and (value=="0" or not value.startswith("0")),reason)
    return int(value)
def assess(plan):
    require(isinstance(plan,dict),"configuration must be an object")
    for key,expected in (("name","miniFORGE"),("symbol","mFRG"),("network","mainnet-beta"),("token_program",PROGRAM),("configuration_type","NON_TRANSACTIONAL_PLANNING_DATA_ONLY")):
        require(plan.get(key)==expected,"invalid "+key)
    require(type(plan.get("schema_version")) is int and plan["schema_version"]==2,"schema")
    require(type(plan.get("decimals")) is int and plan["decimals"]==6,"six decimals required")
    require(positive_integer_string(plan.get("target_supply_ui"),"supply UI") == TOTAL,"total supply")
    require(positive_integer_string(plan.get("target_supply_atomic"),"supply atomic") == TOTAL*SCALE,"supply atomic mismatch")
    allocations=plan.get("allocations")
    require(isinstance(allocations,list) and len(allocations)==len(EXPECTED),"exactly nine allocations required")
    seen=set();period_totals={k:0 for k in PERIODS};sum_atomic=0
    for row in allocations:
        require(isinstance(row,dict),"allocation row must be object")
        key=row.get("id")
        require(isinstance(key,str) and key in EXPECTED and key not in seen,"unknown or duplicate allocation")
        seen.add(key)
        amount=positive_integer_string(row.get("tokens_ui"),key+" tokens")
        atomic=positive_integer_string(row.get("amount_atomic"),key+" atomic")
        require(amount==EXPECTED[key] and atomic==amount*SCALE,"allocation mismatch: "+key)
        require(row.get("account_address") is None and row.get("custody_authority") is None,
                "predeployment template must not assert deployed account/custody: "+key)
        schedule=row.get("release_ceiling_by_period_mfrg")
        require(isinstance(schedule,dict) and set(schedule)==set(PERIODS),"schedule fields: "+key)
        for period,limit in schedule.items():
            require(type(limit) is int and limit>=0,"invalid schedule amount: "+key)
            period_totals[period]+=limit
        require(sum(schedule.values())==amount,"schedule does not reconcile: "+key)
        sum_atomic+=atomic
    require(seen==set(EXPECTED) and sum_atomic==TOTAL*SCALE,"allocations fail to reconcile")
    require(plan.get("release_schedule_total_by_period_mfrg")==period_totals,"period summary mismatch")
    founder=plan.get("founder")
    require(isinstance(founder,dict),"founder disclosures missing")
    require(founder.get("immediate_id")=="founder_immediate" and founder.get("deferred_id")=="founder_deferred_team_label","founder categories")
    require(positive_integer_string(founder.get("total_tokens_ui"),"founder total")==30_000_000,"founder total mismatch")
    require(founder.get("monthly_vesting_first_month")==13 and founder.get("monthly_vesting_last_month")==36,"vesting window")
    require(positive_integer_string(founder.get("monthly_tokens_ui"),"vesting monthly")==625_000,"vesting rate")
    require(positive_integer_string(founder.get("monthly_amount_atomic"),"vesting atomic")==625_000*SCALE,"vesting atomic")
    require(24*625_000==EXPECTED["founder_deferred_team_label"],"vesting sum")
    require("same" in founder.get("beneficial_owner","").lower() or "both" in founder.get("beneficial_owner","").lower(),"same founder disclosure")
    fund=plan.get("fundraising")
    require(isinstance(fund,dict),"fundraising policy missing")
    require(positive_integer_string(fund.get("total_inventory_ui"),"fundraising supply")==50_000_000,"fundraising total")
    require(positive_integer_string(fund.get("pilot_inventory_ui"),"fundraising pilot")==5_000_000,"pilot cap")
    require(fund.get("approved_consideration_assets")==[] and fund.get("checkout_enabled") is False,"payments must stay disabled")
    require(fund.get("price") is None and fund.get("sale_start") is None and fund.get("sale_end") is None,"sale must not be scheduled")
    for flag in ("is_issuance_authorized","is_sale_authorized","is_staking_authorized","is_liquidity_authorized","fee_payer_balance_currently_verified","fixed_cap_enforced","allocation_completed"):
        require(plan.get(flag) is False,"must remain false: "+flag)
    require(plan.get("network_mint_address") is None,"no existing mainnet mint in a predeployment plan")
    require(plan.get("metadata_status")=="unverified" and plan.get("mint_authority_status")=="unverified","authority remains unverified")
    return {"status":"PREDEPLOYMENT_POLICY_CONSISTENT_NOT_RELEASE_APPROVAL",
            "planned_total_atomic":sum_atomic,"allocation_categories":len(EXPECTED),
            "planned_fundraising_pilot_ui":5_000_000,
            "planned_founder_beneficial_ui":30_000_000,
            "planned_period_totals":period_totals,
            "production_deployment_authorized":False,"mint_creation_authorized":False,
            "wallet_key_material_provisioned":False,"treasury_accounts_created":False,
            "security_audit_completed":False,"live_chain_transactions_performed":False}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan",nargs="?",default="apps/desktop/config/miniFORGE.mainnet.plan.json")
    args=parser.parse_args()
    try:
        plan=json.loads(pathlib.Path(args.plan).read_text(encoding="utf-8"))
        print(json.dumps(assess(plan),indent=2,sort_keys=True))
    except (PreflightError,OSError,ValueError,TypeError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2
    return 0
if __name__=="__main__":raise SystemExit(main())
