# miniFORGE 500M update — STEP 01 handoff: discovery and scope

**Date:** 2026-10-28
**Repository:** `tgibbsz32/forgecoin`
**Working branch:** `docs/mfrg-500m-lifetime-tokenomics-20261028`
**Status:** Discovery complete; no mint, sale or treasury transfers authorized.

## Confirmed
- Website is sourced from `docs/` and published by `.github/workflows/pages.yml` upon pushes to `main`.
- Previous docs/site advertised a superseded 50M mFRG allocation (5M sale, 5M liquidity/staking, 40M later reserve); source website, public sale status, sale.js, whitepaper, roadmap, wiki and governance pages were affected.
- Native FRG source documentation describes **50M primary-emission reference, NOT a hard cap**, owing to **0.20 FRG per 120-second block perpetual tail reward**. No consensus changes authorized.
- Existing Solana mainnet mint and token balances are **not independently verified**; published sale status is intentionally disabled.
- Existing desktop plan `apps/desktop/config/miniFORGE.mainnet.plan.json` contains older 50M/three-bucket values and a 0-SOL prior-preflight note. It may be consumed by desktop tooling, so **requires a distinct code/consumer audit before updating**, rather than silently changing a possibly executable configuration.
- Past `docs/RELEASE_STATUS_2026-10-24.md`, older pool research and other history files contain historical planning, and must be clearly marked superseded rather than rewriting historical evidence.

## Selected economic policy
- Target **500,000,000 mFRG**, standard SPL, 6 decimals; fixed supply only once mint balances/authorities are proven.
- Nine mutually exclusive budgets: 50M fundraising, 100M operations, 100M adoption, 85M staking, 60M liquidity, 65M engineering/security, **15M founder immediate**, **15M founder-beneficial deferred team label** (625k monthly months 13–36), 10M emergency.
- Both 3% founder buckets benefit the same person, **6% aggregate**.
- Target release ceilings: Y1 74M; Y2–3 95M; Y4–10 117M; Y11–20 113M; Y21–30 101M.
- No token price or active sale. Crypto consideration may include USDC/SOL after review. FRG and mFRG are distinct and not pegged.

## Resume
Proceed to STEP 02 implementation handoff, update all current public documents, keep sale/quotes/fulfillment hard-disabled, then validate with independent calculations and review PR. Do not infer that creating a planning file changes mainnet supply.
