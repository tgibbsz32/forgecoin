"""Offline acceptance: no real Solana connections, payments or wallet secrets."""
import copy
import io
import json
import os
import sqlite3
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))
import sale_core as core
from sale_ledger import OrderLedger
import wsgi

BUYER=core.encode_pubkey(b'\x11'*32)
MERCHANT=core.encode_pubkey(b'\x22'*32)
MERCHANT_ATA=core.encode_pubkey(b'\x33'*32)
BUYER_ATA=core.encode_pubkey(b'\x44'*32)
OTHER_BUYER=core.encode_pubkey(b'\x55'*32)
OTHER_ATA=core.encode_pubkey(b'\x66'*32)
SIG='3'*88

def final_tx(quote, sig=SIG, *, signer=BUYER, owner=BUYER, usdc_mint=core.SOLANA_MAINNET_USDC):
    amount=quote["usdc_units"]
    return {
        "slot":1234567,
        "transaction":{
            "signatures":[sig],
            "message":{
                "accountKeys":[{"pubkey":BUYER,"signer":signer==BUYER},
                               {"pubkey":quote["reference"],"signer":False},
                               {"pubkey":MERCHANT_ATA,"signer":False},
                               {"pubkey":BUYER_ATA,"signer":False},
                               {"pubkey":MERCHANT,"signer":False}],
                "instructions":[{
                    "program":"spl-token","programId":core.SPL_TOKEN_PROGRAM,
                    "parsed":{"type":"transferChecked","info":{
                        "source":BUYER_ATA,"destination":MERCHANT_ATA,
                        "mint":usdc_mint,"authority":BUYER,
                        "tokenAmount":{"amount":str(amount),"decimals":6}}}
                }]
            }
        },
        "meta":{
            "err":None,"innerInstructions":[],
            "preTokenBalances":[
                {"accountIndex":3,"mint":core.SOLANA_MAINNET_USDC,"owner":owner,
                 "uiTokenAmount":{"amount":str(200000000),"decimals":6}},
                {"accountIndex":2,"mint":core.SOLANA_MAINNET_USDC,"owner":MERCHANT,
                 "uiTokenAmount":{"amount":"8000000","decimals":6}}
            ],
            "postTokenBalances":[
                {"accountIndex":3,"mint":core.SOLANA_MAINNET_USDC,"owner":owner,
                 "uiTokenAmount":{"amount":str(200000000-amount),"decimals":6}},
                {"accountIndex":2,"mint":core.SOLANA_MAINNET_USDC,"owner":MERCHANT,
                 "uiTokenAmount":{"amount":str(8000000+amount),"decimals":6}}
            ]
        }
    }

class SaleCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="mfrg-sale-offline-")
        self.addCleanup(self.temp.cleanup)
        self.now=[1770000000]
        self.terms=core.SandboxTerms(
            price_usdc_micro_per_mfrg=50000,
            buyer_cap_atomic=core.MAX_SALE_ATOMIC,
            usdc_recipient_owner=MERCHANT,
            usdc_recipient_token_account=MERCHANT_ATA)
        self.ledger=OrderLedger(
            Path(self.temp.name)/"test-orders.sqlite",
            sandbox_terms=self.terms,test_only_enable_quotes=True,
            clock=lambda:self.now[0])
    def quote(self,n=200,buyer=BUYER):
        return self.ledger.reserve_sandbox_order(buyer,n*core.ATOMIC)
    def test_01_exact_allocation_and_usdc_mint(self):
        self.assertEqual(core.MAX_SALE_ATOMIC,5000000000000)
        self.assertEqual(core.PILOT_SALE_TOKENS,5000000)
        self.assertEqual(core.SALE_TREASURY_TOKENS,50000000)
        self.assertEqual(core.LIQUIDITY_RESERVE_TOKENS,60000000)
        self.assertEqual(core.FUTURE_DISTRIBUTION_TOKENS,390000000)
        self.assertEqual(sum(core.ALLOCATION_MFRG.values()),500000000)
        self.assertEqual(core.ALLOCATION_MFRG['founder_immediate'] + core.ALLOCATION_MFRG['founder_deferred_team_label'],30000000)
        self.assertEqual(core.TOTAL_SUPPLY_ATOMIC,500000000000000)
        self.assertEqual(core.SOLANA_MAINNET_USDC,"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    def test_02_base58_roundtrip_and_invalid_inputs(self):
        for data in (b'\0'*32,b'\x01'*32,b'\xff'*32):
            self.assertEqual(core.decode_pubkey(core.encode_pubkey(data)),data)
        for value in ("O"*34,"0"*34,"abc", "z"*50, BUYER+"x"):
            with self.subTest(value=value),self.assertRaises(core.SaleError):
                core.decode_pubkey(value)
    def test_03_integer_quotes_and_no_float_rounding(self):
        for value in (True,1.3,-1,0,"100",core.ATOMIC//2):
            with self.subTest(value=value),self.assertRaises(core.SaleError):
                self.ledger.reserve_sandbox_order(BUYER,value)
    def test_04_solana_pay_url_contains_exact_quote_and_unique_reference(self):
        q=self.quote(200)
        self.assertEqual(q["mfrg"],"200")
        self.assertEqual(q["usdc"],"10")
        self.assertEqual(q["state"],"quoted")
        url=urlparse(q["solana_pay_url"])
        self.assertEqual(url.scheme,"solana")
        self.assertEqual(url.path,MERCHANT)
        parsed=parse_qs(url.query)
        self.assertEqual(parsed["amount"],["10"])
        self.assertEqual(parsed["spl-token"],[core.SOLANA_MAINNET_USDC])
        self.assertEqual(parsed["reference"],[q["reference"]])
        self.assertIn("NO REAL FUNDS",parsed["message"][0])
        self.assertFalse(q["production_usable"])
    def test_05_reference_and_order_identity_unique(self):
        first=self.quote()
        second=self.quote()
        self.assertNotEqual(first["id"],second["id"])
        self.assertNotEqual(first["reference"],second["reference"])
    def test_06_5m_reservation_is_max_and_cannot_oversell(self):
        self.quote(5000000)
        with self.assertRaises(core.InsufficientAllocation):
            self.quote(1)
        self.assertEqual(self.ledger.inventory()["unreserved_atomic"],0)
    def test_07_expired_quote_frees_remaining_inventory(self):
        self.quote(5000000)
        self.now[0]+=901
        self.quote(5000000)
        self.assertEqual(self.ledger.inventory()["unreserved_atomic"],0)
    def test_08_order_expiry_boundary_and_no_price_changes(self):
        first=self.quote(1)
        self.now[0]+=900
        self.assertEqual(self.ledger.status(first["id"])["state"],"expired")
        self.assertEqual(self.ledger.inventory()["unreserved_atomic"],core.MAX_SALE_ATOMIC)
    def test_09_durable_sqlite_restart_and_no_double_reservation(self):
        first=self.quote(310)
        other=OrderLedger(Path(self.temp.name)/"test-orders.sqlite",
            sandbox_terms=self.terms,test_only_enable_quotes=True,
            clock=lambda:self.now[0])
        self.assertEqual(other.status(first["id"])["state"],"quoted")
        self.assertEqual(other.inventory()["reserved_or_used_atomic"],310000000)
    def test_10_non_test_production_engine_refuses_real_quotes(self):
        live=OrderLedger(Path(self.temp.name)/"disabled.sqlite")
        with self.assertRaises(core.SaleNotReady):
            live.reserve_sandbox_order(BUYER,core.ATOMIC)
        self.assertFalse(Path(self.temp.name,"disabled.sqlite").exists())
        self.assertFalse(core.PRODUCTION_PAYMENT_COLLECTION_ENABLED)
    def test_11_multiple_threads_cannot_oversell_5m(self):
        results=[]
        barrier=threading.Barrier(3)
        def worker():
            barrier.wait()
            try:results.append(("ok",self.quote(3000000)))
            except core.InsufficientAllocation:results.append(("oversold_blocked",None))
        a=threading.Thread(target=worker);b=threading.Thread(target=worker)
        a.start();b.start();barrier.wait();a.join();b.join()
        self.assertEqual(sorted(r[0] for r in results),["ok","oversold_blocked"])
        self.assertEqual(self.ledger.inventory()["reserved_or_used_atomic"],3000000000000)
    def test_12_valid_exact_finalized_usdc_moves_to_fulfillment_pending(self):
        q=self.quote()
        receipt=self.ledger.sandbox_record_finalized_payment(q["id"],SIG,final_tx(q))
        self.assertEqual(receipt["state"],"payment_finalized_pending_delivery")
        self.assertEqual(receipt["fulfillment"],"NOT_IMPLEMENTED_NO_ASSETS_SENT")
        self.assertEqual(self.ledger.status(q["id"])["state"],"payment_finalized_pending_delivery")
        self.assertEqual(self.ledger.inventory()["reserved_or_used_atomic"],200000000)
    def test_13_replay_same_signature_is_idempotent_for_same_order(self):
        q=self.quote()
        receipt=final_tx(q)
        first=self.ledger.sandbox_record_finalized_payment(q["id"],SIG,receipt)
        second=self.ledger.sandbox_record_finalized_payment(q["id"],SIG,receipt)
        self.assertEqual(first["state"],second["state"])
    def test_14_replayed_payment_signature_cannot_fund_second_order(self):
        first=self.quote()
        self.ledger.sandbox_record_finalized_payment(first["id"],SIG,final_tx(first))
        second=self.quote()
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(second["id"],SIG,final_tx(second))
        self.assertEqual(self.ledger.status(second["id"])["state"],"quoted")
    def test_15_late_payment_requires_refund_review_not_delivery(self):
        q=self.quote()
        self.now[0]+=901
        receipt=self.ledger.sandbox_record_finalized_payment(q["id"],SIG,final_tx(q))
        self.assertEqual(receipt["state"],"late_payment_refund_review")
        self.assertEqual(self.ledger.inventory()["reserved_or_used_atomic"],0)
    def test_16_bad_signature_fails_and_does_not_change_state(self):
        q=self.quote()
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],"4"*88,final_tx(q))
        self.assertEqual(self.ledger.status(q["id"])["state"],"quoted")
    def test_17_payment_wrong_reference_is_refused(self):
        q=self.quote();payload=final_tx(q)
        payload["transaction"]["message"]["accountKeys"][1]["pubkey"]=OTHER_BUYER
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],SIG,payload)
    def test_18_payment_wrong_mint_is_refused(self):
        q=self.quote()
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(
                q["id"],SIG,final_tx(q,usdc_mint=OTHER_BUYER))
    def test_19_payment_wrong_amount_is_refused(self):
        q=self.quote();p=final_tx(q)
        p["transaction"]["message"]["instructions"][0]["parsed"]["info"]["tokenAmount"]["amount"]="999"
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],SIG,p)
    def test_20_payment_wrong_merchant_destination_is_refused(self):
        q=self.quote();p=final_tx(q)
        p["transaction"]["message"]["instructions"][0]["parsed"]["info"]["destination"]=OTHER_ATA
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],SIG,p)
    def test_21_payment_no_buyer_signature_is_refused(self):
        q=self.quote()
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],SIG,final_tx(q,signer=OTHER_BUYER))
    def test_22_failed_onchain_transaction_is_refused(self):
        q=self.quote();p=final_tx(q);p["meta"]["err"]={"InstructionError":[0,"Custom"]}
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],SIG,p)
    def test_23_amount_credit_and_debit_deltas_verified(self):
        q=self.quote();p=final_tx(q)
        p["meta"]["postTokenBalances"][1]["uiTokenAmount"]["amount"]="8000001"
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],SIG,p)
        p=final_tx(q);p["meta"]["postTokenBalances"][0]["uiTokenAmount"]["amount"]="189000001"
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],SIG,p)
    def test_24_missing_finalized_transaction_slot_refused(self):
        q=self.quote();p=final_tx(q);p["slot"]=0
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],SIG,p)
    def test_25_duplicate_merchant_transfer_instruction_refused(self):
        q=self.quote();p=final_tx(q)
        p["meta"]["innerInstructions"].append({
            "index":0,
            "instructions":[copy.deepcopy(p["transaction"]["message"]["instructions"][0])]
        })
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],SIG,p)
    def test_26_wrong_source_token_account_owner_refused(self):
        q=self.quote()
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],SIG,final_tx(q,owner=OTHER_BUYER))
    def test_27_wrong_merchant_token_owner_refused(self):
        q=self.quote();p=final_tx(q)
        p["meta"]["postTokenBalances"][1]["owner"]=OTHER_BUYER
        with self.assertRaises(core.PaymentMismatch):
            self.ledger.sandbox_record_finalized_payment(q["id"],SIG,p)
    def test_28_ledger_cannot_fulfill_or_sign_any_tokens(self):
        self.assertFalse(hasattr(self.ledger,"send_mfrg"))
        self.assertFalse(hasattr(self.ledger,"execute_purchase"))
        self.assertFalse(hasattr(self.ledger,"create_mainnet_payment"))
        self.assertFalse(hasattr(self.ledger,"mark_delivered"))
    def test_29_sandbox_price_cap_and_qty_bounds(self):
        self.terms.validate()
        with self.assertRaises(core.SaleError):
            core.SandboxTerms(1000,core.MAX_SALE_ATOMIC+1,MERCHANT,MERCHANT_ATA).validate()
        with self.assertRaises(core.SaleError):
            core.SandboxTerms(0,core.ATOMIC,MERCHANT,MERCHANT_ATA).validate()
        with self.assertRaises(core.SaleError):
            self.quote(5000001)
    def test_30_sqlite_order_query_is_not_injectable(self):
        with self.assertRaises(core.SaleError):
            self.ledger.status("' OR 1=1 --")

class SaleWSGITests(unittest.TestCase):
    def request(self,path="/api/v1/status",method="GET",origin=None):
        result={}
        environ={"PATH_INFO":path,"REQUEST_METHOD":method}
        if origin:environ["HTTP_ORIGIN"]=origin
        def start(status,headers):
            result["status"]=status;result["headers"]=dict(headers)
        body=b"".join(wsgi.application(environ,start))
        return result["status"],json.loads(body),result["headers"]
    def test_31_live_status_is_paused_and_has_no_mint_or_price(self):
        status,data,headers=self.request()
        self.assertTrue(status.startswith("200"))
        self.assertIs(data["sale_enabled"],False)
        self.assertIs(data["quotes_enabled"],False)
        self.assertIs(data["payments_enabled"],False)
        self.assertIs(data["fulfillment_enabled"],False)
        self.assertIsNone(data["sale_price_usdc"])
        self.assertIsNone(data["token_mainnet_mint"])
        self.assertEqual(data["sale_treasury_mfrg"],50000000)
        self.assertEqual(data["initial_pilot_mfrg"],5000000)
        self.assertEqual(data["supply_total_mfrg"],500000000)
        self.assertEqual(data["future_distribution_reserve_mfrg"],390000000)
        self.assertIsNone(data["currently_issued_mainnet_mfrg"])
        self.assertEqual(headers["Cache-Control"],"no-store, max-age=0")
    def test_32_every_public_post_payment_endpoint_blocked(self):
        for path in ("/api/v1/quote","/api/v1/order","/api/v1/pay","/api/v1/fulfill"):
            with self.subTest(path=path):
                code,data,_=self.request(path,method="POST")
                self.assertEqual(code,"405 Method Not Allowed")
                self.assertFalse(data["payment_collected"])
    def test_33_admin_and_orders_do_not_exist(self):
        for path in ("/api/v1/admin/activate","/api/v1/order/random","/private"):
            with self.subTest(path=path):
                code,data,_=self.request(path)
                self.assertEqual(code,"404 Not Found")
    def test_34_cors_allows_only_official_pages_origin(self):
        _,_,trusted=self.request(origin="https://tgibbsz32.github.io")
        _,_,hostile=self.request(origin="https://attacker.example")
        self.assertEqual(trusted["Access-Control-Allow-Origin"],"https://tgibbsz32.github.io")
        self.assertNotIn("Access-Control-Allow-Origin",hostile)
    def test_35_invalid_or_simulated_env_var_cannot_enable_payment(self):
        old=os.environ.get("MINIFORGE_SALE_LIVE")
        os.environ["MINIFORGE_SALE_LIVE"]="true"
        try:
            _,payload,_=self.request()
            self.assertFalse(payload["sale_enabled"])
        finally:
            if old is None:os.environ.pop("MINIFORGE_SALE_LIVE",None)
            else:os.environ["MINIFORGE_SALE_LIVE"]=old


    def test_36_read_only_api_exposes_nine_distinct_allocations(self):
        code,data,_=self.request("/api/v1/allocations")
        self.assertEqual(code,"200 OK")
        self.assertEqual(data["target_total_tokens"],500000000)
        self.assertEqual(data["reserved_for_sale_tokens"],50000000)
        self.assertEqual(data["pilot_sale_cap_tokens"],5000000)
        self.assertEqual(data["future_liquidity_tokens"],60000000)
        self.assertEqual(data["founder_beneficial_total_mfrg"],30000000)
        self.assertEqual(sum(data["allocations_mfrg"].values()),500000000)
        self.assertIs(data["sale_contract_deployed"],False)

    def test_37_lifetime_allocation_never_raises_pilot_bound(self):
        self.assertEqual(core.MAX_SALE_ATOMIC,5000000*core.ATOMIC)
        self.assertEqual(core.SALE_TREASURY_TOKENS*core.ATOMIC,10*core.MAX_SALE_ATOMIC)
        self.assertLess(core.MAX_SALE_ATOMIC,core.TOTAL_SUPPLY_ATOMIC)
        with self.assertRaises(core.InsufficientAllocation):
            self.ledger.reserve_sandbox_order(BUYER,5000001*core.ATOMIC)

    def test_38_fundraising_and_founder_not_double_counted(self):
        allocations=core.ALLOCATION_MFRG
        self.assertEqual(len(allocations),9)
        self.assertEqual(allocations["fundraising"],50000000)
        self.assertEqual(allocations["founder_immediate"],15000000)
        self.assertEqual(allocations["founder_deferred_team_label"],15000000)
        self.assertEqual(allocations["liquidity"],60000000)
        self.assertEqual(allocations["staking"],85000000)

if __name__=="__main__":
    unittest.main(verbosity=2)
