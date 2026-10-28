"""Durable, race-safe *5M initial pilot* mFRG simulation ledger (offline tests only)."""
from __future__ import annotations
import sqlite3
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode
from typing import Any
from sale_core import (
    ATOMIC, MAX_SALE_ATOMIC, PRODUCTION_PAYMENT_COLLECTION_ENABLED,
    SOLANA_MAINNET_USDC, SandboxTerms, SaleError, SaleNotReady,
    PaymentMismatch, InsufficientAllocation, fmt_amount, integer_amount,
    encode_pubkey, decode_pubkey, verify_finalized_usdc_transaction
)
ORDER_STATES = frozenset((
    "quoted", "expired", "payment_finalized_pending_delivery",
    "late_payment_refund_review", "fulfilled", "fulfillment_review"
))
class OrderLedger:
    """No production checkout path. Tests opt in to 5M pilot simulated orders explicitly.

    Wallet signing/automated fulfillment is intentionally NOT IMPLEMENTED.
    Never run this with real buyer payments until those controls are reviewed.
    """
    def __init__(self, database_path: str | Path,
                 *, sandbox_terms: SandboxTerms | None = None,
                 test_only_enable_quotes: bool = False,
                 clock=None, entropy=None):
        self.path = str(database_path)
        self.clock = clock or (lambda: int(time.time()))
        self.entropy = entropy or secrets.token_bytes
        self.terms = sandbox_terms
        self.test_only = test_only_enable_quotes
        if self.terms:
            self.terms.validate()
        if test_only_enable_quotes and self.terms is None:
            raise SaleError("Sandbox terms required for tests")
        if not test_only_enable_quotes and PRODUCTION_PAYMENT_COLLECTION_ENABLED:
            raise AssertionError("Production checkout interlock unexpectedly removed")
        if not test_only_enable_quotes:
            # Production app never reads or opens a writable ledger.
            return
        self._create()

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.row_factory = sqlite3.Row
        return connection

    def _create(self):
        connection = self._connect()
        try:
            connection.executescript("""
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=FULL;
                CREATE TABLE IF NOT EXISTS sale_orders (
                    id TEXT PRIMARY KEY,
                    reference TEXT NOT NULL UNIQUE,
                    buyer TEXT NOT NULL,
                    mint_units INTEGER NOT NULL CHECK(mint_units>0 AND mint_units<=5000000000000) -- fixed 5M PILOT cap; do not increase to 50M lifetime,
                    usdc_units INTEGER NOT NULL CHECK(usdc_units>0),
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    payment_signature TEXT UNIQUE,
                    payment_slot INTEGER,
                    fulfilled_signature TEXT UNIQUE,
                    fulfilled_slot INTEGER
                );
                CREATE INDEX IF NOT EXISTS idx_sale_orders_state_expiry
                    ON sale_orders(state,expires_at);
            """)
        finally:
            connection.close()

    def _require_sandbox(self):
        if not self.test_only:
            raise SaleNotReady(
                "The miniFORGE mainnet mint, USDC sale terms, fulfillment signer, "
                "treasury custody and regulatory approvals are not ready. "
                "No sale quotes or payments are available."
            )

    @staticmethod
    def _check_units(units: int):
        integer_amount(units)
        if units % ATOMIC:
            raise SaleError("Sandbox currently uses whole mFRG quantities only")
        if units < ATOMIC:
            raise SaleError("Minimum order 1 mFRG")
        if units > MAX_SALE_ATOMIC:
            raise InsufficientAllocation("Order exceeds the 5M initial pilot cap")

    @staticmethod
    def _cost(mint_units: int, price_usdc_micro_per_token: int) -> int:
        # Integer ceil in base units, so decimals never under-collect.
        usdc_units, remainder = divmod(
            mint_units * price_usdc_micro_per_token, ATOMIC
        )
        return usdc_units + (1 if remainder else 0)

    @staticmethod
    def _expire(connection, now: int):
        connection.execute(
            "UPDATE sale_orders SET state='expired' WHERE state='quoted' AND expires_at<=?",
            (now,)
        )

    def reserve_sandbox_order(self, buyer: str, mint_units: int) -> dict:
        self._require_sandbox()
        decode_pubkey(buyer)
        self._check_units(mint_units)
        if mint_units > self.terms.buyer_cap_atomic:
            raise SaleError("Quantity exceeds the sandbox per-order limit")
        now = int(self.clock())
        expires = now + self.terms.quote_ttl_seconds
        price = self.terms.price_usdc_micro_per_mfrg
        cost = self._cost(mint_units, price)
        if cost <= 0:
            raise SaleError("Quote cannot result in zero USDC")
        # A random 32-byte reference is a public account marker, never a signing key.
        reference = encode_pubkey(self.entropy(32))
        order_id = secrets.token_hex(20)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._expire(connection, now)
            # Pending final payments and fulfilled orders all count against cap.
            # Expired orders are no longer reserved. Late payments require refund review.
            row = connection.execute("""
                SELECT COALESCE(SUM(mint_units),0) FROM sale_orders
                WHERE state IN (
                    'quoted','payment_finalized_pending_delivery',
                    'fulfilled','fulfillment_review'
                )
            """).fetchone()
            used = int(row[0])
            if used + mint_units > MAX_SALE_ATOMIC:
                raise InsufficientAllocation("Not enough unreserved 5M pilot supply")
            connection.execute("""
                INSERT INTO sale_orders(id,reference,buyer,mint_units,usdc_units,
                    created_at,expires_at,state)
                VALUES(?,?,?,?,?,?,?,'quoted')
            """, (order_id, reference, buyer, mint_units, cost, now, expires))
            connection.commit()
        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.close()
        recipient = self.terms.usdc_recipient_owner
        url = "solana:" + recipient + "?" + urlencode({
            "amount": fmt_amount(cost),
            "spl-token": self.terms.usdc_mint,
            "reference": reference,
            "label": "miniFORGE sandbox test",
            "message": "DEV ONLY / NO REAL FUNDS " + order_id[:12],
        })
        return {
            "id": order_id, "reference": reference, "buyer": buyer,
            "mfrg_units": mint_units, "mfrg": fmt_amount(mint_units),
            "usdc_units": cost, "usdc": fmt_amount(cost),
            "expires_at": expires, "state": "quoted",
            "solana_pay_url": url,
            "environment": "SANDBOX_UNIT_TEST_ONLY",
            "production_usable": False,
        }

    def status(self, order_id: str) -> dict:
        self._require_sandbox()
        if not isinstance(order_id, str) or len(order_id) != 40:
            raise SaleError("Invalid order ID")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._expire(connection, int(self.clock()))
            row = connection.execute(
                "SELECT * FROM sale_orders WHERE id=?", (order_id,)
            ).fetchone()
            connection.commit()
        finally:
            connection.close()
        if not row:
            raise SaleError("Order not found")
        return {"id": row["id"], "reference": row["reference"],
                "state": row["state"],
                "mfrg_units": row["mint_units"],
                "usdc_units": row["usdc_units"],
                "expires_at": row["expires_at"],
                "payment_signature": row["payment_signature"],
                "fulfilled_signature": row["fulfilled_signature"]}

    def sandbox_record_finalized_payment(
        self, order_id: str, signature: str, finalized_rpc_transaction: dict
    ) -> dict:
        """Payment validation only; DOES NOT SHIP mFRG or authorize a production sale."""
        self._require_sandbox()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = int(self.clock())
            self._expire(connection, now)
            row = connection.execute(
                "SELECT * FROM sale_orders WHERE id=?", (order_id,)
            ).fetchone()
            if row is None:
                raise SaleError("Order not found")
            if row["state"] in ("payment_finalized_pending_delivery","fulfilled"):
                if row["payment_signature"] == signature:
                    connection.commit()
                    return {"state":row["state"], "id":order_id,
                            "payment_signature":signature,
                            "fulfillment":"NOT_IMPLEMENTED_NO_ASSETS_SENT"}
                raise PaymentMismatch("Order already has another payment signature")
            if row["state"] not in ("quoted", "expired"):
                raise SaleError("Order is not awaiting a finalized payment")
            # Receipt must exactly match this order's immutable quote and buyer.
            evidence = verify_finalized_usdc_transaction(
                finalized_rpc_transaction, buyer=row["buyer"],
                reference=row["reference"], signature=signature,
                amount_usdc_atomic=row["usdc_units"],
                merchant_token_account=self.terms.usdc_recipient_token_account,
                merchant_wallet=self.terms.usdc_recipient_owner,
                usdc_mint=self.terms.usdc_mint,
            )
            # Expired but paid orders cannot be silently reused/fulfilled.
            state = "payment_finalized_pending_delivery" if row["state"] == "quoted" \
                else "late_payment_refund_review"
            connection.execute("""
                UPDATE sale_orders SET state=?, payment_signature=?,payment_slot=?
                WHERE id=?
            """,(state,signature,evidence["slot"],order_id))
            connection.commit()
            return {"state":state, "id":order_id, "payment_signature":signature,
                    "fulfillment":"NOT_IMPLEMENTED_NO_ASSETS_SENT"}
        except sqlite3.IntegrityError as error:
            connection.rollback()
            raise PaymentMismatch("Payment signature reused for another order") from error
        except Exception:
            if connection.in_transaction: connection.rollback()
            raise
        finally:
            connection.close()

    def inventory(self) -> dict[str,int]:
        self._require_sandbox()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._expire(connection,int(self.clock()))
            row = connection.execute("""
                SELECT COALESCE(SUM(mint_units),0) FROM sale_orders
                WHERE state IN ('quoted','payment_finalized_pending_delivery',
                                'fulfilled','fulfillment_review')
            """).fetchone()
            connection.commit()
            used = int(row[0])
        finally:
            connection.close()
        return {"total_sale_allocation_atomic":MAX_SALE_ATOMIC,
                "reserved_or_used_atomic":used,
                "unreserved_atomic":MAX_SALE_ATOMIC-used}
