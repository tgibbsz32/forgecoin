# miniFORGE 500M update — STEP 03 handoff: validation and release readiness

**Date:** 2026-10-28
**Repository/branch:** `tgibbsz32/forgecoin` / `docs/mfrg-500m-lifetime-tokenomics-20261028`
**Status:** Branch-level static validation passed; full build/deployment still requires GitHub Pages workflow and live website verification.

## Static verification completed

1. **Policy math:** Nine allocation quantities in `docs/sale-status.json` sum to **500,000,000 mFRG**. Founder beneficial total = **15M immediate + 15M deferred = 30M (6%)**. Deferred vesting: **625,000 × 24 monthly periods (months 13–36) = 15,000,000**.
2. **Lifetime release schedule:** Period ceilings of **74M + 95M + 117M + 113M + 101M = 500M**. The full year-bucket table in `MFRG_LIFETIME_TOKENOMICS_500M.md` reconciles to each reserve.
3. **Read-only sale invariant:** `sale_enabled`, `payments_enabled`, `quotes_enabled` and `fulfillment_enabled` remain **false** in public JSON; `token_mainnet_mint` and `sale_price_usdc` are `null`. `sale.js` retains `CHECKOUT_LOCKED = true`. It now expects revised 500M total/50M fundraising/60M liquidity/390M remaining accounts.
4. **Website basic structure:** Verified opening and closing counts for structural HTML tags (html, head, body, header, main, footer, section, div, article, table, etc.) on **nine public site HTML pages**. All balances matched.
5. **Sale markup integration:** All ten ID-based elements referenced by `docs/sale.js` exist in `docs/miniforge-sale.html`; no missing required elements.
6. **Navigation links:** Checked relative links in six primary site pages against the `docs/` inventory on the branch. All ordinary direct links resolved. The only special paths were existing `images/forgecoin-logo.png` assets under the `docs/images/` subdirectory.
7. **Historical context:** Deprecated 50M mFRG plans in October technical evidence were marked with a superseding 500M policy notice, rather than rewriting the historical discussion. Legacy governance demonstration pages now direct users to current policy.
8. **Native FRG separation:** Public docs retain the repository's 50M **primary-emission reference, not hard cap**, with perpetual 0.20 FRG per 120-second block. No native consensus code touched.

## Deliberate limitations

- Static checks are **not** an audit or a browser-based end-to-end test. Visual layout, accessibility and GitHub Pages build must still be verified after deployment.
- **Existing desktop implementation plan** `apps/desktop/config/miniFORGE.mainnet.plan.json` retains old 50M/5M/5M/40M values and is a known **implementation migration blocker**. It was deliberately excluded because consumer code and downstream allocation assumptions are not yet audited. Never use it to mint, issue or transfer mFRG.
- Old offline checkout/quote prototype also enforces 5M pilot-style limits and has not been migrated or production audited.
- No 500M on-chain mint is verified, no treasury/vault accounts are funded, no sale can open and no staking is deployed. No economic contract or token exchange has been implemented.
- Do not state the website is live until the PR is merged, GitHub Pages deployment reports success and resulting URLs are inspected.

## Resume at STEP 04

Open a review PR to `main`, inspect diff and checks, merge only if safe and allowed, confirm GitHub Pages deployment and critical public pages, and write `MFRG_500M_STEP_04_PUBLICATION_2026-10-28.md` with actual commit/PR and post-merge status.
