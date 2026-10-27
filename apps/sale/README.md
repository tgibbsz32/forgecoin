# miniFORGE Solana USDC sale — implementation and security gates

**October 27, 2026 — read-only development preview. No token sale is currently open.**

The sale module is separate from native FRG mining, Oracle pool operations, the explorer and wallet/miner releases. It does not change FRG consensus, mining, payout signing or any treasury.

## New: actual Solana atomic exchange prototype (development-only)

The source under [atomic-swap](atomic-swap/README.md) contains a compiled Anchor/SPL escrow program with on-chain 5M sale cap, exact integer USDC price, per-wallet cap, buyer maximum debit, immutable treasury, admin pause and atomic USDC-payment / mFRG-delivery instructions. In a loopback-only Solana validator using disposable mock USDC/mFRG, the program passed **22 real transaction integration assertions**, including a forced second-transfer failure that rolled back the attempted USDC payment. Rust unit tests passed 5/5. A default devnet-mint-pinned SBF build also succeeded, but its public devnet deployment was blocked because a separate test deployer has zero SOL and a 2 SOL devnet faucet request failed. **No mainnet or public devnet contract, token issuance, production checkout or real payment has been performed.** The hosted website and production status WSGI remain hard-disabled; the swap program is not production-audited.

## Implemented sources

- docs/miniforge-sale.html, docs/sale.css and docs/sale.js: responsive informational preview with the 50M target supply, planned 5M/5M/40M allocations, checkout stages, public-wallet-address preview and disabled purchase controls. No payment recipient, sender keys, swap function or sale price is embedded.
- docs/sale-status.json: paused same-origin snapshot, not an on-chain attestation.
- apps/sale/sale_core.py: pure Solana Base58 address validation, exact atomic USDC pricing and finalized transaction **verification logic**. Checks buyer signature, unique order reference, genuine USDC mint, SPL Token program, merchant account and owner, exact amount, pre/post token-account balance deltas and transaction success. Does not contact RPC or sign a transaction.
- apps/sale/sale_ledger.py: disposable **test-only** SQLite WAL quote and USDC-payment reconciliation model. BEGIN IMMEDIATE serializes concurrent reservations against the 5M sale cap. Quote IDs and public references unique, quotes expire, double-spent signatures rejected, expired payments flagged for refund review. Simulated payment confirmation moves only to payment_finalized_pending_delivery, never to completed distribution. The deployed WSGI module never instantiates the test ledger.
- apps/sale/wsgi.py: production read-only public API. GET /api/v1/status and /api/v1/allocations; every POST returns HTTP 405, unknown/admin/order paths 404, CORS limited to official GitHub Pages. No deposit endpoint, order creation, payment or token delivery is exposed.
- apps/sale/tests: offline and adversarial economic, inventory, signature, replay, status and static website tests.

## Prerequisites before any real sale

1. **Create actual mainnet mFRG token.** No mainnet mFRG mint was created at the last preflight. The development mint is devnet-only, with zero issuance. Configure standard SPL 6 decimals and reconcile exactly 50M tokens in verified accounts: 5M sale, 5M future liquidity and 40M later distribution. Resolve the fixed-cap mint-authority policy, Metaplex metadata and custody key backups.
2. **Fund merchant wallet and secure sale inventory.** Use a separately controlled treasury, with documented multisig or equivalent signer policy, proper associated token accounts and chain-verified mFRG/USDC balances. Signing keys must never be embedded in Pages or public Oracle web processes.
3. **Approve sale terms and legal requirements.** Sale price, schedule, eligibility, jurisdiction, sanctions/AML/KYC obligations as applicable, refunds, purchase limits, disclosures and custody requirements remain undefined. Obtain legal review before accepting funds. Do not imply a token listing, guaranteed market, liquidity, price appreciation or investment returns.
4. **Implement independently audited atomic purchase/escrow on Solana.** Prefer swapping buyer USDC for mFRG in a **single atomic transaction**, without accepting USDC for unfulfilled merchant IOUs. Alternatives using a custodial payout signer require their own rigorous buyer protections and compliance procedures. This branch **contains neither** a production smart contract nor a fulfillment signer.
5. **Integrate verifiable RPC and token delivery.** Pin Solana mainnet RPC, verify finalized transactions using getTransaction with encoding=jsonParsed and commitment=finalized (not client-supplied JSON), check exact buyer/seller ownership, USDC mint, payment amount, reference and source/destination balance changes. Independently verify mFRG arrival in the customer's token account, prevent double-counting and handle timeouts, failures, late payments, duplicates and refunds. The parser alone cannot attest RPC trustworthiness.
6. **Production ordering and controls.** Enforce the exact 5M dedicated sale cap, quote expiry, anti-abuse limits, user notices, durable accounting, audit logging, eligibility checks, operator approval, trusted quote price publication, uptime/rate limits and accessible customer receipts. Run real **devnet** small-value acceptance tests and independent review before any mainnet checkout.
7. **Release gate.** Keep production disabled until mint creation, confirmed inventory, secure USDC merchant ownership, signed sale terms, on-chain atomic delivery, legal/security review and independent full-system validation. Activation must require a separately reviewed build, not a user-editable environment variable.

## Fixed safety protections in this branch

The Python constant PRODUCTION_PAYMENT_COLLECTION_ENABLED is false. The WSGI app has no quote/payment endpoint. The static JS permanently disables quantities, quotes and payment actions regardless of status JSON, and only permits a user-initiated public-address wallet preview (no signing). The real public site **must not solicit funds or show a payment address** until a fully authorized production issuance and sale.

## Tests

From repository root, with Python 3.11+ and Node.js:

    python apps/sale/tests/test_sale.py
    python apps/sale/tests/test_site.py
    node --check docs/sale.js

All tests use synthetic public Solana keys and temporary SQLite and never send live USDC, SPL transfers, create tokens, mine blocks or access owner secrets.

See the public-facing token plan at docs/MINIFORGE_SPL_TREASURIES.md and the expanded implementation specification at docs/MINIFORGE_SALE_MECHANISM.md.
