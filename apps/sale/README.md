# miniFORGE — offline-only 500M tokenomics sale prototype

**October 28, 2026. Not a sale, offer, executable checkout, audited escrow, mint service or approved fundraising product.** No production quote, buyer deposit, token transfer, live mint, custody key, payment API, or smart-contract deployment is enabled by the files in this directory.

## Three different quantities that must never be conflated

| Accounting unit | Tokens | Six-decimal atomic units |
| --- | ---: | ---: |
| **Intended total mFRG supply** | **500,000,000** | **500,000,000,000,000** |
| **Maximum lifetime cryptocurrency fundraising budget** | **50,000,000** | **50,000,000,000,000** |
| **Maximum initial pilot inventory** | **5,000,000** | **5,000,000,000,000** |

The **pilot cap stays at 5M**, even though the reserve allocated to fundraising over years 1–10 is 50M. Increasing it requires a separately approved offering, contract and audit; do not change the old cap to 50M by global search and replace.

The nine-category allocation and 30-year budgets are in [canonical tokenomics](../../docs/MFRG_LIFETIME_TOKENOMICS_500M.md). This includes **30M (6%) founder-beneficial mFRG**: 15M immediately liquid and 15M labelled “team” yet beneficially owned by the same founder, unlocking 625k monthly during months 13–36. The remaining 450M non-fundraising supply is not sale inventory.

## Source layout and safety

- `sale_core.py`: immutable policy constants, Base58 validation, test-only quote terms and pure finalized-USDC-receipt verification. All amounts use integer atomic units; **no network RPC authentication is performed** and simulated receipt data must never be accepted for production fulfillment.
- `sale_ledger.py`: disposable test-only SQLite quote/reservation/reconciliation model; SQL row CHECK and locked accounting enforce **5M pilot** limit. When `test_only_enable_quotes=False`, it refuses checkout. It **does not sign, deliver tokens or connect to a blockchain**.
- `wsgi.py`: informational GET-only API at `/api/v1/status` and `/api/v1/allocations`; every POST is rejected with 405. Mainnet minted supply is **unknown/unverified**, not proven zero. No mainnet mint/payment price or authorized payment asset is provided.
- `tests/test_sale.py`: sandbox economic, quote, concurrent inventory, signature, receipt and replay checks.
- `tests/test_site.py`: static website allocation, founder disclosure, disabled controls and backend-status parity.
- `tests/test_browser.cjs`: mock browser asserts the wallet connection is address-only and checkout cannot be unlocked by tampered status.

**Not ported from legacy [PR #122](https://github.com/tgibbsz32/forgecoin/pull/122):** its separate Rust Anchor escrow code, old website changes, old status JSON and obsolete 50M allocation. The Rust escrow in #122 remains devnet/test-only and has an intentional **5M** cap, but has NOT been production-audited or merged here. Do not deploy its program, widen cap, or assume it handles all later fundraising tranches.

## Offline tests

```sh
python3 apps/sale/tests/test_sale.py
python3 apps/sale/tests/test_site.py
node apps/sale/tests/test_browser.cjs
python3 tools/test_mfrg_policy.py
```

All tests run locally with mock keys and data and do not contact Solana.

## Required before a separately authorized sale

1. Independently verify the actual user's already-existing mFRG Solana mainnet mint, program ID, supply, decimals, mint/freeze authority, token metadata and beneficial holders. If mint authority was revoked below 500M, plan a disclosed migration; do not presume it can be changed.
2. Establish distinct funded allocations and founder vesting contract, a properly controlled crypto proceeds treasury and independent custody, plus on-chain reconciliation.
3. Obtain professional securities, state-law, FinCEN/sanctions, tax, consumer protection and distribution terms review. Cryptocurrency received instead of fiat can still create legal obligations.
4. Obtain independent security review of transaction settlement, treasury administration, buyer cap, quote origin, oracle/rate handling, chain finality, rejected and late payment refunds.
5. Make a separately reviewed production implementation with secure atomic payment/delivery, participant safeguards and a new explicit release gate. **Never activate this sandbox by toggling a flag or using `sale-status.json` as permission.**
