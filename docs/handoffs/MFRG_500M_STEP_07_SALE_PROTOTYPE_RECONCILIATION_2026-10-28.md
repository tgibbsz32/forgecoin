# miniFORGE 500M — STEP 07 handoff: review of legacy sale prototype PR #122

**Date:** October 28, 2026
**Repository:** `tgibbsz32/forgecoin`
**State:** Audit and PR review comment complete; sale prototype remains unmerged and disabled.

## Objective

Review the existing development-only [PR #122](https://github.com/tgibbsz32/forgecoin/pull/122) for incompatibilities with the newly published 500M lifetime mFRG tokenomics and prepare a safe migration plan. The original PR is a USDC-only development preview with a **5M pilot escrow cap** and separate test-only backend components; this review does not authorize a public sale.

## Evidence reviewed

- `apps/sale/sale_core.py`
- `apps/sale/sale_ledger.py`
- `apps/sale/wsgi.py`
- `apps/sale/README.md`
- `apps/sale/atomic-swap/programs/miniforge_swap/src/lib.rs`
- `apps/sale/atomic-swap/tests/guardrails.cjs`
- `apps/sale/tests/test_sale.py`
- PR metadata and changed-file list (27 modified/additional paths).
- **Public review comment:** [PR #122, comment 6463942887](https://github.com/tgibbsz32/forgecoin/pull/122).

## Main accounting distinction to enforce

1. **Total intended mFRG supply = 500,000,000 tokens = 500,000,000,000,000 atomic units (6 decimals)** — project planning policy, not proof of minting.
2. **Lifetime cryptocurrency fundraising inventory = 50,000,000 tokens = 50,000,000,000,000 atomic units** — not all active or escrowed now.
3. **Initial pilot sale limit = 5,000,000 tokens = 5,000,000,000,000 atomic units** — KEEP this constraint in the old pilot escrow/SQLite order test model if an independently approved pilot is pursued.
4. Non-sale reserves (450M combined), including founder-beneficial 30M, staking 85M and liquidity 60M, may **never** be borrowed silently for sale orders or counted as buyer inventory.

## Confirmed prototype issues

| Component | Current branch state | Required change before any merge |
| --- | --- | --- |
| `sale_core.py` | `TOTAL_SUPPLY_ATOMIC=50M × 1e6`; 5M liquidity, 40M development; 5M sale cap | Update total supply and reserve-model constants, introduce explicit **50M lifetime inventory** separately from **5M pilot cap** |
| `sale_ledger.py` | SQLite order amounts/checks capped at 5M | Keep **5M pilot cap**; make tranche limits explicit and ensure no allocation outside authorized tranche |
| `wsgi.py` | Read-only status and allocation response report old 50M / 5M / 5M / 40M | Reconcile read-only metadata with public nine-bucket policy and disabled status flags |
| `test_sale.py` | Unit assertions expect old 50M total and three buckets | Update economic consistency tests; retain 5M reservation, replay, invalid-payment and no-production safeguards |
| Rust `lib.rs` | `SALE_CAP_ATOMIC=5_000_000_000_000`, devnet mint pinned; mainnet build gated | **Keep** 5M pilot cap and devnet-only compile gate; separate audited mainnet escrow program would be required |
| PR site/docs changes | Previous policy embedded in old website JSON and HTML | Rebase onto `main` after #125/#126, preserve current 500M website, founder disclosure and hard-disabled checkout |
| Sale security | Prototype is development-only; not audited or authorized | Obtain independently reviewed production escrow, mint verification, custody, legal and treasury approvals first |

**Security positive:** The source includes explicit development-only compilation guards and an atomic payment/delivery path in the Rust prototype. This is **not** proof of production security or an independent audit. No real-money transaction, mint, price or deployment was performed in this step.

## Explicit actions taken

- Inspected repo/PR source and old economic fields.
- Added a detailed review comment to **PR #122** recording reconciliation requirements and the instruction **not to merge or activate** the old checkout.
- Preserved PR #122's source unchanged. No escrow limits were raised, and no sale was enabled.

## Next recommended STEP 08

Create a dedicated development branch from the **updated `main`** to safely adapt the prototype's **offline-only** constants, API status and tests to three different values: **500M intended total**, **50M lifetime fundraising budget** and **5M pilot transaction cap**. If porting PR #122 code, rebase or selectively integrate only after inspecting overlap with current updated website files. Keep the 5M pilot escrow bound and all production activation guards. Run existing adversarial unit tests and the `tools/test_mfrg_policy.py` CI. Do not deploy production contracts or accept funds.

**Critical external dependency:** The user says a Solana token was created, but no authentic **mainnet mint address** has yet been supplied or independently verified here. Request/use the exact mainnet mint to verify program, decimals, circulating supply, mint/freeze authority and accounts before taking any on-chain issuance, migration or treasury action. Never assume old devnet mint represents this production asset. Legal and tax review is needed before fundraising in other coins.

## Ongoing handoff convention

After each future substantive stage, create `docs/handoffs/MFRG_500M_STEP_NN_<TOPIC>_YYYY-MM-DD.md` listing exact artifacts/commits, observed test results, what did **not** occur, blockers and next actions. Avoid claiming a token is issued, a website is live, or a contract is audited without direct evidence.
