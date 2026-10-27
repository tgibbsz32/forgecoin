"""Read-only mFRG presale status service. No secrets, accounts or payments.

This is an intentionally CLOSED production service. It cannot create a real
checkout quote even if an operator passes an environment variable. Future
activation must be a separately audited/signed release with an atomic
fulfillment mechanism and legal/compliance gates.
"""
import json
from urllib.parse import urlsplit
from sale_core import (
    MAX_SALE_ATOMIC, TOTAL_SUPPLY_ATOMIC, SALE_TREASURY_TOKENS,
    LIQUIDITY_RESERVE_TOKENS, FUTURE_DISTRIBUTION_TOKENS,
    PRODUCTION_PAYMENT_COLLECTION_ENABLED, SOLANA_MAINNET_USDC
)
assert PRODUCTION_PAYMENT_COLLECTION_ENABLED is False

STATUS = {
    "schema": "miniforge-sale-status-v1",
    "name": "miniFORGE", "symbol": "mFRG",
    "network": "solana-mainnet-beta",
    "state": "not_open",
    "sale_enabled": False,
    "quotes_enabled": False,
    "payments_enabled": False,
    "fulfillment_enabled": False,
    "token_mainnet_mint": None,
    "sale_price_usdc": None,
    "sale_start": None,
    "sale_end": None,
    "payment_asset": "USDC",
    "payment_mint_mainnet": SOLANA_MAINNET_USDC,
    "accepted_payment_network": "solana-mainnet-beta-only-when-authorized",
    "supply_total_mfrg": 50_000_000,
    "sale_treasury_mfrg": SALE_TREASURY_TOKENS,
    "future_liquidity_reserve_mfrg": LIQUIDITY_RESERVE_TOKENS,
    "future_distribution_reserve_mfrg": FUTURE_DISTRIBUTION_TOKENS,
    "currently_issued_mainnet_mfrg": 0,
    "remaining_sale_treasury_verified": None,
    "notices": [
        "No mainnet mFRG mint or circulating sale tokens have been verified.",
        "No sale price or sales terms have been approved.",
        "Do not send SOL, USDC or other tokens to any ForgeCoin wallet for an mFRG sale.",
        "No sale, swap, token checkout, wallet signature or payment request is active."
    ]
}
ALLOCATION = {
    "schema": "miniforge-allocations-v1",
    "target_total_tokens": 50_000_000,
    "reserved_for_sale_tokens": SALE_TREASURY_TOKENS,
    "future_liquidity_tokens": LIQUIDITY_RESERVE_TOKENS,
    "future_distribution_tokens": FUTURE_DISTRIBUTION_TOKENS,
    "on_chain_status": "not_issued_on_mainnet",
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
