# miniFORGE 500M — STEP 05 handoff: desktop planning configuration migration

**Date:** October 28, 2026
**Repository:** `tgibbsz32/forgecoin`
**Branch:** `chore/mfrg-500m-safe-config-validation-20261028`
**Status:** Plan and documentation migrated in review branch; CI check and PR completion to be recorded in STEP 06.

## Objective / audit findings

Reconcile the obsolete **50M mFRG / 5M sale / 5M combined liquidity-staking / 40M future** desktop configuration with the current **500M / nine-category** economics, without actual minting, moving tokens, enabling purchases or changing native FRG.

Examined `apps/desktop/SolanaWallet.cs`: the Windows wallet **does not read** `config/miniFORGE.mainnet.plan.json` for live balances. It instead requires a separate `config/miniFORGE.mainnet.json` with `network = mainnet-beta`, `productionReady = true` and a valid independently verified mint. The latter production mint file is **not provided by the planning update**. Thus updating the .plan file is not issuance or wallet activation. A documented devnet mint exists, but a mainnet SPL supply/authority has **not been independently verified** in this repository. Do not assume the user's existing token is absent or that a new mint is necessary.

Also inspected [PR #122](https://github.com/tgibbsz32/forgecoin/pull/122): the older sale/atomic-checkout prototype remains **open**, separate from this branch, and its five-million inventory accounting needs a safety and integration audit.

## Changed files

1. **`apps/desktop/config/miniFORGE.mainnet.plan.json`**: schema v2, explicit `NON_TRANSACTIONAL_PLANNING_DATA_ONLY`, standard SPL six-decimal target of **500,000,000 mFRG = 500,000,000,000,000 atomic units** (below u64 maximum), nine distinct allocation records and independent null vault/owner fields.
2. Period limits per bucket and network total: 74M / 95M / 117M / 113M / 101M across year 1, years 2–3, 4–10, 11–20 and 21–30 respectively. Total 500M.
3. Fundraising cap **50M**, with tranche caps **5M pilot + 15M additional Y1 + 20M Y2–3 + 10M Y4–10**. Payment assets remain **unapproved**; prospective USDC/SOL are not a live offer.
4. Founder fields: first **15M (3%) freely unlocked at launch**, second **15M (3%) team label but same founder beneficiary**, **625,000 monthly for months 13–36**, 30M (6%) total founder-beneficial.
5. Proposed finite staking: 85M reserve, 30/90/180/365 day locks and 1.00/1.10/1.20/1.40 weights, weekly reward claims, seven-day cooldown, no guaranteed APY and no FRG PoW security.
6. **`apps/desktop/SolanaWallet.cs`**: UI messages now state **“Mainnet mint unconfigured”** instead of asserting that no Solana mainnet mFRG token exists. The live mint gate and read-only balance query logic remain unchanged.
7. **`apps/desktop/SOLANA_WALLET_READINESS.md`** updated to 500M intended supply, null mint/authority risk, the desktop wallet's separate production-ready gate and the older prototype blockers.
8. **`tools/test_mfrg_policy.py`** adds offline read-only consistency tests for supply, atomic units, allocation accounting, year releases, founder vesting, staged sale inventory, staking weights and no-sale safeguards.
9. **`.github/workflows/mfrg-policy-guardrails.yml`** runs the standard-library Python tests in CI, read-only repository permissions.

## Explicit safety invariants

- `is_issuance_authorized`, `is_sale_authorized`, `is_staking_authorized`, `is_liquidity_authorized` and `fundraising.checkout_enabled` all **false**.
- Mainnet mFRG mint unknown (`network_mint_address: null`); supply not on-chain verified; mint authority not verified; vault and signer identities all null; no token allocations completed.
- Historical fee payer balance (0 SOL on October 27 preflight) is **not** asserted as current balance.
- No on-chain RPC use, private keys, transaction requests, funds collection, Solana asset transfers or native FRG consensus changes.
- Neither `sale-status.json` nor public checkout JS is opened by these commits.

## Next step — STEP 06 validation and PR

1. Open PR for this branch and observe the new CI job.
2. Verify that all checks pass; resolve failures before merge.
3. Confirm desktop mainnet mint gate is still fail-closed and status metadata remains disabled.
4. Merge only reviewed, passing non-transactional changes; record exact PR, commit SHA, CI run and resulting release state in a separate STEP 06 handoff.
5. **Following implementation stage:** independently inspect and verify any existing actual mFRG mainnet mint and its authority; build custody/vesting accounts only after legal/security review; examine PR #122 under the revised 50M lifetime fundraising allocation. No sale or new mint is authorized by this step.
