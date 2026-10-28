"""Read-only mFRG presale status service. No secrets, accounts or payments.

This is an intentionally CLOSED production service. It cannot create a real
checkout quote even if an operator passes an environment variable. Future
activation must be a separately audited/signed release with an atomic
fulfillment mechanism and legal/compliance gates.
"""
import json
from urllib.parse import urlsplit
from sale_core import (
    MAX_SALE_ATOMIC, TOTAL_SUPPLY_ATOMIC, TOTAL_SUPPLY_TOKENS,
    SALE_TREASURY_TOKENS, PILOT_SALE_TOKENS,
    LIQUIDITY_RESERVE_TOKENS, FUTURE_DISTRIBUTION_TOKENS,
    ALLOCATION_MFRG, PRODUCTION_PAYMENT_COLLECTION_ENABLED,
    SOLANA_MAINNET_USDC
)
assert PRODUCTION_PAYMENT_COLLECTION_ENABLED is False

STATUS = {
    "schema": "miniforge-sale-status-v1",
    "updated_utc": "2026-10-28",
    "source": "offline-prototype-read-only",
    "name": "miniFORGE", "symbol": "mFRG",
    "network": "solana-mainnet-beta",
    "state": "not_open",
    "sale_enabled": False, "quotes_enabled": False,
    "payments_enabled": False, "fulfillment_enabled": False,
    "token_mainnet_mint": None,
    "sale_price_usdc": None, "sale_start": None, "sale_end": None,
    "payment_asset": None,  # no approved asset; candidate USDC is not an offer
    "candidate_payment_asset": "Solana USDC",
    "payment_mint_mainnet": SOLANA_MAINNET_USDC,
    "accepted_payment_network": None,
    "supply_total_mfrg": TOTAL_SUPPLY_TOKENS,
    "sale_treasury_mfrg": SALE_TREASURY_TOKENS,  # 50M LIFETIME only
    "initial_pilot_mfrg": PILOT_SALE_TOKENS,  # 5M pilot escrow ceiling
    "future_liquidity_reserve_mfrg": LIQUIDITY_RESERVE_TOKENS,
    "future_distribution_reserve_mfrg": FUTURE_DISTRIBUTION_TOKENS,
    "allocation_mfrg": ALLOCATION_MFRG,
    "founder_beneficial_total_mfrg":
        ALLOCATION_MFRG["founder_immediate"] +
        ALLOCATION_MFRG["founder_deferred_team_label"],
    "founder_deferred_vesting": "625000 monthly in months 13-36; founder beneficiary of both allocations",
    "currently_issued_mainnet_mfrg": None,  # unknown: do not claim zero issuance
    "remaining_sale_treasury_verified": None,
    "treasury_program_status": "Not verified or deployed",
    "notices": [
        "The intended 500M supply and nine allocations are NOT on-chain attestations.",
        "The 50M lifetime fundraising inventory does NOT raise the 5M pilot cap.",
        "No verified mainnet mint, sale price or approved terms have been established here.",
        "Do not send SOL, USDC or other crypto expecting mFRG from this prototype.",
        "No quote, swap, payment request, signature, fulfillment or deposit is active."
    ]
}
ALLOCATION = {
    "schema": "miniforge-allocations-v2",
    "target_total_tokens": TOTAL_SUPPLY_TOKENS,
    "reserved_for_sale_tokens": SALE_TREASURY_TOKENS,  # lifetime
    "pilot_sale_cap_tokens": PILOT_SALE_TOKENS,
    "future_liquidity_tokens": LIQUIDITY_RESERVE_TOKENS,
    "future_distribution_tokens": FUTURE_DISTRIBUTION_TOKENS,
    "allocations_mfrg": ALLOCATION_MFRG,
    "founder_beneficial_total_mfrg": STATUS["founder_beneficial_total_mfrg"],
    "on_chain_status": "mint_and_balances_unverified",
    "sale_contract_deployed": False
}

def application(environ, start_response):
    path = environ.get("PATH_INFO", "") or "/"
    method = environ.get("REQUEST_METHOD", "GET").upper()
    origin = environ.get("HTTP_ORIGIN")
    # Only informational requests from the official GitHub Pages origin.
    cors = [("Access-Control-Allow-Origin","https://tgibbsz32.github.io"),
            ("Vary", "Origin")] if origin == "https://tgibbsz32.github.io" else []
    headers = [
        ("Content-Type","application/json; charset=utf-8"),
        ("Cache-Control","no-store, max-age=0"),
        ("X-Content-Type-Options","nosniff"),
        ("X-Frame-Options","DENY"),
        ("Referrer-Policy","no-referrer"),
        ("Content-Security-Policy","default-src 'none'; frame-ancestors 'none'"),
    ] + cors
    if method != "GET":
        code, payload = "405 Method Not Allowed", {
            "code":"SALE_NOT_OPEN", "error":"Requests and payments are disabled.",
            "payment_collected":False
        }
        headers.append(("Allow","GET"))
    elif path in ("/api/v1/status","/status"):
        code,payload="200 OK",STATUS
    elif path in ("/api/v1/allocations","/allocations"):
        code,payload="200 OK",ALLOCATION
    else:
        code,payload="404 Not Found",{"code":"NOT_FOUND","error":"This sale endpoint does not exist."}
    content = json.dumps(payload,sort_keys=True,separators=(",",":")).encode("utf-8")
    headers.append(("Content-Length",str(len(content))))
    start_response(code,headers)
    return [content]

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    # Local-only development process; intentionally no public binding.
    with make_server("127.0.0.1", 18910, application) as server:
        server.serve_forever()
