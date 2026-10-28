# miniFORGE 500M update — STEP 04 handoff: published documentation

**Date:** October 28, 2026
**State:** Documentation change merged and GitHub Pages publishing checks successful. No on-chain execution occurred.

## Exact publication references

- **Repository:** `tgibbsz32/forgecoin`
- **Pull request:** [#125 — 500M mFRG lifetime tokenomics](https://github.com/tgibbsz32/forgecoin/pull/125) — merged to `main`.
- **Merged commit:** `5004a8c873bbaa74c72a883f906506bc9fee5068`.
- **Website publish job:** [40653308380](https://github.com/tgibbsz32/forgecoin/actions/runs/40653308380) — **completed successfully** for merged commit.
- **GitHub Pages build/deployment:** [40653307470](https://github.com/tgibbsz32/forgecoin/actions/runs/40653307470) — **completed successfully** for merged commit.
- **Primary docs:** [lifetime tokenomics](../MFRG_LIFETIME_TOKENOMICS_500M.md), [treasuries](../MINIFORGE_SPL_TREASURIES.md), [sale engineering gates](../MINIFORGE_SALE_MECHANISM.md), [web tokenomics](../miniforge-tokenomics.html), [web sale preview](../miniforge-sale.html).

**Live-site limitation:** A direct external fetch of the rendered GitHub Pages URLs was unavailable in this session. GitHub's own jobs report successful publication, but rendered pages still merit browser-based spot checks for aesthetics, content and accessibility.

## Published scope and financial boundaries

The planned **500,000,000 mFRG** total comprises 50M fundraising, 100M operations, 100M adoption, 85M finite staking incentives, 60M liquidity, 65M engineering/security, **15M (3%) immediately unlocked founder holdings**, **15M (3%) team-labeled but founder-beneficial monthly vesting months 13–36**, and 10M emergency. The same founder benefits from **30M total (6%)**. All future circulation is subject to released budgets and on-chain proof.

The public status `sale-status.json` is static and **disabled for sales, payments, quotes and fulfillment**; no approved token price, mint address, payment recipient or sale start date is published. No Solana mainnet mint, vesting vault, exchange, staking or liquidity pool is established by this documentation update.

**Native FRG unchanged:** Existing documented rules state 50M FRG primary-emission reference and continuing 0.20 FRG reward per 120-second block. Do not market native FRG as strictly capped until consensus code and chain policy demonstrate it.

## Remaining implementation blockers — recommended next step

1. **Reconcile actual Solana mFRG mint and token authorities.** Identify any already minted supply, freeze/mint authority, token decimals, beneficial ownership and treasury accounts. If mint authority is revoked below 500M, do not attempt to increase that mint: propose transparent migration.
2. **Audit consumer code before changing desktop plan:** `apps/desktop/config/miniFORGE.mainnet.plan.json` still has **old 50M/5M/5M/40M intended balances**. Determine who reads it and whether any wallet, mint or UI functionality assumes its old schema and identifiers. Update with unit/atomic math and verified contract guards only in a separate code PR.
3. **Audit existing disabled quote/checkout prototype:** prior inventory cap, quote validation, fulfillment and receipt code were drafted for the previous 5M sale model. Keep production disabled; do not enable by changing JSON.
4. **Define and deploy project custody and vesting:** the founder's 15M immediately liquid tokens and 15M months-13-to-36 vesting need independently verifiable contracts/accounts; disclose both as founder-beneficial and protect other reserves from commingling.
5. **Create actual legal/compliance and treasury framework:** review crypto-denominated offerings, tax, custody, sanctions and money transmission, specify allowable payment assets, price mechanism, trading/eligibility restrictions and refunds before solicitation. Establish external USDC/SOL operating reserves, budgets and grant rules.
6. **Audit staking and liquidity architecture:** 30/90/180/365-day proposal, weights, weekly claims and seven-day post-expiry cooldown. Verify reward exhaustion, security, treasury-controlled LP risks and honest public disclosures. No guaranteed APY.
7. **Verify website in browser:** primary pages, footer/nav links, mobile responsiveness, year tables and visible no-sale notices, including `miniforge-tokenomics.html`, `miniforge-sale.html`, `exchange.html`, `community.html`, and `current-mainnet.html`.

## Follow-up handoff convention

For each future substantive step, add `docs/handoffs/MFRG_500M_STEP_NN_<topic>_YYYY-MM-DD.md` with: objective, exact files/commits/PR, decisions, tests and proof, blockers, and exact next action. Do not claim unperformed tests or authorize transfer of tokens from a documentation change.
