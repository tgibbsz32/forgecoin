"""miniFORGE sale ledger and finalized USDC receipt verifier.

Production checkout is unconditionally DISABLED in this release. These primitives
are exercised only in isolated, no-money tests, and are NOT an audited sale.
No keys, signing, secret derivation, token transfers, or minting are implemented.
"""
from __future__ import annotations
import json
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode
from typing import Any

MFRG_DECIMALS = 6
USDC_DECIMALS = 6
ATOMIC = 10**6
SALE_TREASURY_TOKENS = 5_000_000
LIQUIDITY_RESERVE_TOKENS = 5_000_000
FUTURE_DISTRIBUTION_TOKENS = 40_000_000
MAX_SALE_ATOMIC = SALE_TREASURY_TOKENS * ATOMIC
TOTAL_SUPPLY_ATOMIC = 50_000_000 * ATOMIC
SPL_TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
SOLANA_MAINNET_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
_BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
# Security interlock: this is deliberately a non-activatable preview release.
PRODUCTION_PAYMENT_COLLECTION_ENABLED = False

class SaleError(ValueError):
    """A quote/receipt is not valid."""
class SaleNotReady(SaleError):
    """No production mint, custody, price, fulfillment or legal readiness."""
class PaymentMismatch(SaleError):
    """Never mark an unverified on-chain transfer paid."""
class InsufficientAllocation(SaleError):
    """There are insufficient unsold tokens in the 5M sale reserve."""

def encode_pubkey(data: bytes) -> str:
    if len(data) != 32:
        raise SaleError("A Solana public key must contain exactly 32 bytes")
    n = int.from_bytes(data, "big")
    text = ""
    while n:
        n, index = divmod(n, 58)
        text = _BASE58[index] + text
    return ("1" * (len(data) - len(data.lstrip(b"\x00")))) + text

def decode_pubkey(value: str) -> bytes:
    if not isinstance(value, str) or not 32 <= len(value) <= 44:
        raise SaleError("Invalid Solana public address length")
    number = 0
    for ch in value:
        if ch not in _BASE58:
            raise SaleError("Invalid Base58 character")
        number = number * 58 + _BASE58.index(ch)
    leading = len(value) - len(value.lstrip("1"))
    if number.bit_length() > 256:
        raise SaleError("Invalid Solana public address length")
    result = b"\x00" * leading + number.to_bytes((number.bit_length() + 7) // 8, "big")
    if len(result) != 32 or encode_pubkey(result) != value:
        raise SaleError("Invalid Solana public address")
    return result

def integer_amount(value: Any) -> int:
    # Do not silently round fractions or accept floats/scientific notation.
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SaleError("Quantity must be a positive integer of token atomic units")
    return value

def fmt_amount(amount: int, decimals: int = 6) -> str:
    whole, remainder = divmod(amount, 10**decimals)
    return f"{whole}.{remainder:0{decimals}d}".rstrip("0").rstrip(".")

@dataclass(frozen=True)
class SandboxTerms:
    """Disposable QA-only economic terms, never a real mFRG price or offering."""
    price_usdc_micro_per_mfrg: int
    buyer_cap_atomic: int
    usdc_recipient_owner: str
    usdc_recipient_token_account: str
    usdc_mint: str = SOLANA_MAINNET_USDC
    quote_ttl_seconds: int = 900

    def validate(self) -> None:
        integer_amount(self.price_usdc_micro_per_mfrg)
        # Bound cost calculations so a valid quote always fits SQLite signed 64-bit.
        if self.price_usdc_micro_per_mfrg > 1_000_000_000_000:
            raise SaleError("Unreasonably large sandbox price would overflow the ledger")
        integer_amount(self.buyer_cap_atomic)
        if self.buyer_cap_atomic > MAX_SALE_ATOMIC:
            raise SaleError("Sandbox per-order cap exceeds sale reserve")
        decode_pubkey(self.usdc_recipient_owner)
        decode_pubkey(self.usdc_recipient_token_account)
        decode_pubkey(self.usdc_mint)
        if self.quote_ttl_seconds < 60 or self.quote_ttl_seconds > 3600:
            raise SaleError("Quote TTL out of bounds")

def _account_key(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("pubkey", "")
    return ""

def _signed(item: Any, buyer: str) -> bool:
    return isinstance(item, dict) and item.get("pubkey") == buyer and item.get("signer") is True

def _extract_token_balance(rows: Any, index: int, mint: str, owner: str) -> int:
    if not isinstance(rows, list):
        raise PaymentMismatch("Missing token balance evidence")
    matches = [
        x for x in rows
        if isinstance(x, dict)
        and x.get("accountIndex") == index
        and x.get("mint") == mint
        and x.get("owner") == owner
        and isinstance(x.get("uiTokenAmount"), dict)
        and x["uiTokenAmount"].get("decimals") == USDC_DECIMALS
    ]
    if len(matches) != 1:
        raise PaymentMismatch("Missing or ambiguous verified token account balance")
    raw = matches[0]["uiTokenAmount"].get("amount")
    if not isinstance(raw, str) or not raw.isdecimal():
        raise PaymentMismatch("Invalid raw token balance")
    return int(raw)

def verify_finalized_usdc_transaction(
    response: dict[str, Any], *,
    buyer: str, reference: str, signature: str, amount_usdc_atomic: int,
    merchant_token_account: str, merchant_wallet: str,
    usdc_mint: str = SOLANA_MAINNET_USDC,
) -> dict[str, Any]:
    """Validate a SOLANA-RPC getTransaction response queried at FINALIZED commitment.

    Callers MUST query an independently trusted Solana MAINNET RPC endpoint with
    encoding=jsonParsed, commitment=finalized and maxSupportedTransactionVersion=0.
    A parsed response alone cannot prove that the RPC is authentic; pin the
    endpoint, certificate and network identity outside this pure validator.
    """
    for address in (buyer, reference, merchant_wallet, merchant_token_account, usdc_mint):
        decode_pubkey(address)
    integer_amount(amount_usdc_atomic)
    if not isinstance(signature, str) or not 65 <= len(signature) <= 88 or any(c not in _BASE58 for c in signature):
        raise PaymentMismatch("Invalid transaction signature")
    if not isinstance(response, dict) or not isinstance(response.get("slot"), int) or response["slot"] <= 0:
        raise PaymentMismatch("Missing finalized slot")
    tx = response.get("transaction")
    meta = response.get("meta")
    if not isinstance(tx, dict) or not isinstance(meta, dict) or meta.get("err") is not None:
        raise PaymentMismatch("Transaction failed or has no verified metadata")
    signatures = tx.get("signatures")
    if not isinstance(signatures, list) or signature not in signatures:
        raise PaymentMismatch("Requested signature does not match transaction")
    message = tx.get("message")
    if not isinstance(message, dict):
        raise PaymentMismatch("Missing transaction message")
    keys = message.get("accountKeys")
    if not isinstance(keys, list):
        raise PaymentMismatch("Missing account keys")
    names = [_account_key(x) for x in keys]
    if names.count(reference) != 1 or not any(_signed(x, buyer) for x in keys):
        raise PaymentMismatch("Unique quote reference or buyer signature is missing")
    if names.count(merchant_token_account) != 1:
        raise PaymentMismatch("Merchant USDC token account is missing or ambiguous")

    outer = message.get("instructions", [])
    inner = meta.get("innerInstructions", [])
    if not isinstance(outer, list) or not isinstance(inner, list):
        raise PaymentMismatch("Malformed transfer instruction lists")
    instructions = list(outer)
    for group in inner:
        if not isinstance(group, dict) or not isinstance(group.get("instructions"), list):
            raise PaymentMismatch("Malformed inner transfer")
        instructions += group["instructions"]
    approved = []
    for ix in instructions:
        if not isinstance(ix, dict):
            raise PaymentMismatch("Malformed instruction")
        if ix.get("programId") != SPL_TOKEN_PROGRAM:
            continue
        parsed = ix.get("parsed")
        if not isinstance(parsed, dict) or parsed.get("type") != "transferChecked":
            continue
        info = parsed.get("info")
        if not isinstance(info, dict) or info.get("destination") != merchant_token_account:
            continue
        quantity = info.get("tokenAmount")
        if (info.get("mint") != usdc_mint or info.get("authority") != buyer or
            not isinstance(quantity, dict) or quantity.get("decimals") != USDC_DECIMALS or
            str(quantity.get("amount")) != str(amount_usdc_atomic)):
            raise PaymentMismatch("Unexpected USDC recipient, amount, mint or signer")
        approved.append(info)
    if len(approved) != 1:
        raise PaymentMismatch("Must have exactly one correctly authorized USDC payment")
    payment = approved[0]
    if names.count(payment.get("source")) != 1:
        raise PaymentMismatch("USDC source token account is missing or ambiguous")
    source_index = names.index(payment["source"])
    recipient_index = names.index(merchant_token_account)
    pre = meta.get("preTokenBalances")
    post = meta.get("postTokenBalances")
    source_before = _extract_token_balance(pre, source_index, usdc_mint, buyer)
    source_after = _extract_token_balance(post, source_index, usdc_mint, buyer)
    destination_before = _extract_token_balance(pre, recipient_index, usdc_mint, merchant_wallet)
    destination_after = _extract_token_balance(post, recipient_index, usdc_mint, merchant_wallet)
    if source_before - source_after != amount_usdc_atomic:
        raise PaymentMismatch("USDC source debit does not equal quoted amount")
    if destination_after - destination_before != amount_usdc_atomic:
        raise PaymentMismatch("USDC merchant account credit does not equal quoted amount")
    return {"signature": signature, "slot": response["slot"],
            "amount_usdc_atomic": amount_usdc_atomic, "buyer": buyer,
            "reference": reference, "merchant_token_account": merchant_token_account}
