# miniFORGE 500M update — STEP 02 handoff: documentation and website edits

**Date:** 2026-10-28
**Repository/branch:** `tgibbsz32/forgecoin` / `docs/mfrg-500m-lifetime-tokenomics-20261028`
**Status:** Editing complete on review branch; pending final validation, PR and live deployment.

## Implemented on branch
- New canonical `docs/MFRG_LIFETIME_TOKENOMICS_500M.md`: 500M allocation (nine buckets), 3% liquid founder + 3% founder-beneficial deferred team, month-13–36 monthly vesting, 30-year release budget, 50M staged crypto exchange inventory, distinct treasury custody and proceeds, staking weights/duration/finite rewards, LPs, conditional service-fee burns, chain separation, and release gates.
- Updated active docs: `README.md`, `ROADMAP.md`, `governance-charter.md`, `docs/WHITEPAPER.md`, `docs/CURRENT_MAINNET.md`, `docs/MINIFORGE_SPL_TREASURIES.md`, `docs/MINIFORGE_SALE_MECHANISM.md`, `docs/MFRG_EXCHANGE_DESIGN.md`, `docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md`, `docs/index.md`.
- Updated website: `docs/miniforge-tokenomics.html` now explains all nine budgets, founder vesting, annual ceilings and staking; `docs/miniforge-sale.html` revised for 50M lifetime fundraising and a 5M pilot; homepage `docs/index.html`, governance `docs/community.html`, `docs/exchange.html`, `docs/current-mainnet.html`; legacy governance demo pages `docs/member-eligibility.html`, `docs/member-registration.html`, `docs/practice-governance.html`.
- Updated `docs/sale-status.json` to static **500M total**, **50M fundraising**, **60M liquidity**, **390M outside fundraising/liquidity**, plus all nine allocations and founder ownership. `sale_enabled/payments_enabled/quotes_enabled/fulfillment_enabled` remain **false**, mainnet mint and price remain **null**.
- Updated `docs/sale.js` metadata verification to expect the new proposed numbers, leaving `CHECKOUT_LOCKED = true`, disabled quote form, and no payment code.
- Updated wiki `docs/wiki/FAQ.md`, `docs/wiki/Current-Status.md`, `docs/wiki/Roadmap.md`; marked October 2024 technical handoffs and releases historical with current-policy notices.

## Deliberately excluded
- No native FRG consensus, daemon, miner, FRG supply, reward algorithm, mainnet genesis or node alterations.
- No mFRG mint or authority change, no SPL transfer, no treasury creation, no payment acceptance, no staking deployment or blockchain bridge.
- Existing desktop Solana plan JSON and non-production backend's 5M inventory handling require **separate consumer audit/migration** before any active launch; see STEP 01.
- No legal review or independent security audit has been performed.

## Resume / STEP 03 criteria
1. Validate exact 500M sum, all 30-year release sums, founder monthly vesting, and corresponding JSON/JS expectations.
2. Inspect HTML correctness and relative navigation links; ensure no hidden checkout activation.
3. Search active pages for incorrect legacy 50M/5M/40M statements.
4. Open PR and observe requested GitHub checks. Merge/publish only if review is satisfactory, then verify GitHub Pages workflow and live URLs.
5. Write STEP 03 and STEP 04 completion handoffs and link the PR.
