# miniFORGE 500M — STEP 10 handoff: offline treasury readiness and founder vesting

**Date:** October 28, 2026
**Repository:** `tgibbsz32/forgecoin`
**PR:** [#129 — mFRG nine-treasury and vesting preflight](https://github.com/tgibbsz32/forgecoin/pull/129)
**Status:** Offline-only implementation prepared for merge on successful final CI; no Solana token transfers, accounts or contracts deployed.

## Continuation from Step 09

[Step 09](MFRG_500M_STEP_09_SOLANA_MINT_PREFLIGHT_2026-10-28.md) added a read-only Solana mint snapshot checker. The repo still has **no independently verified user-owned mainnet mFRG mint address, token supply, authority, signer or holder data**. The historical devnet mint is explicitly rejected as mainnet. No authentically verified token inventory exists yet, so treasury deployment and founder transfers must remain blocked.

The most recent verified GitHub Pages deployment for Step 09 [completed successfully](https://github.com/tgibbsz32/forgecoin/actions/runs/40703515474). The earlier overlapping-deployment failure in Step 08 was transient; site/static release readiness does not imply sale activation.

## What Step 10 adds

1. [`docs/mfrg-treasury-registry.template.json`](../mfrg-treasury-registry.template.json) lists **nine separate intended mFRG budgets**, 500M total, six-decimal atomic values, and explicit null placeholders for mint, launch time, account public addresses, custodial authorities and verified balances. **Every approval/funding flag is false**; the separate USDC/SOL proceeds treasury is not a tenth mFRG supply category.
2. [`tools/mfrg_treasury_vesting_preflight.py`](../../tools/mfrg_treasury_vesting_preflight.py) compares the template with the actual planning data `apps/desktop/config/miniFORGE.mainnet.plan.json` and public closed sale metadata `docs/sale-status.json`. Fails closed on funding claims, verified ownership assertions, nonempty addresses, unauthorized supply/beneficiary changes, duplicate accounts, invalid release totals or activation switches. It performs **no RPC, minting, signing, transfers or write operations**.
3. [`tools/test_mfrg_treasury_vesting_preflight.py`](../../tools/test_mfrg_treasury_vesting_preflight.py) contains **17 offline test methods** covering nine-account sums, all period ceilings, 5M pilot versus 50M lifetime fundraising, founder beneficiary and monthly vesting invariants, calendar month-end/leap-year rules, UTC safety, and false funding/escrow/payment claims.
4. [`docs/MFRG_TREASURY_VESTING_IMPLEMENTATION.md`](../MFRG_TREASURY_VESTING_IMPLEMENTATION.md) documents deployment gates, nine earmarked accounts, custody and multisig requirements, founder vesting, audits and legal prerequisites.
5. [`docs/MFRG_TREASURY_VESTING_GATES.md`](../MFRG_TREASURY_VESTING_GATES.md) and [`docs/index.md`](../index.md) link the new runbook and clarify unlock dates.
6. [`.github/workflows/mfrg-treasury-vesting.yml`](../../.github/workflows/mfrg-treasury-vesting.yml) runs the new tests, the read-only readiness command, previously merged mint-snapshot tests and 500M accounting/disabled-sale checks.

## Economic policy — unchanged and reconciled

| Purpose | mFRG |
| --- | ---: |
| Lifetime fundraising budget, of which only 5M pilot was proposed first | 50,000,000 |
| Long-term operations | 100,000,000 |
| Ecosystem grants | 100,000,000 |
| Finite staking/participation rewards | 85,000,000 |
| Liquidity reserve | 60,000,000 |
| Engineering/security | 65,000,000 |
| **Founder immediate / unrestricted when actually distributed** | **15,000,000** |
| **Team label, beneficially owned by SAME founder / escrowed months 13–36** | **15,000,000** |
| Emergency | 10,000,000 |
| **Total** | **500,000,000** |

The founder controls **6% (30M mFRG) beneficially**. The first **3% (15M)** is unrestricted at actual launch if validly issued and transferred; the second **3% (15M)** is scheduled for **24 x 625,000 mFRG** releases *at the end of calendar months 13–36*, based on a verified **UTC T0 that is not established yet**.

Consequence: end year 2 (24 months) = **7.5M deferred vested, 22.5M total founder-accessible**; end year 3 (36 months) = **15M deferred vested, 30M total founder-accessible**. Leap years and last-day calendar dates must never shift entitlement dates. A simulated release table is **not** an on-chain smart contract.

## CLI examples — offline and non-binding

```sh
python3 tools/mfrg_treasury_vesting_preflight.py
python3 tools/test_mfrg_treasury_vesting_preflight.py

# Hypothetical simulation ONLY, NOT an approved launch time:
python3 tools/mfrg_treasury_vesting_preflight.py \
  --hypothetical-launch-utc 2026-11-01T00:00:00Z \
  --as-of-utc 2028-11-01T00:00:00Z
```

The successful report says planning balances reconcile, **not** `mint_independently_verified=true`, `all_nine_accounts_funded_verified=true` or `sale_or_issuance_authorized=true`. It may be run without access to a blockchain.

## Verification evidence

- Initial PR head `5396650d590a108e793fe1bd2029d7daed1fb548` passed [treasury preflight CI #40705141640](https://github.com/tgibbsz32/forgecoin/actions/runs/40705141640) and [mint preflight CI #40705141243](https://github.com/tgibbsz32/forgecoin/actions/runs/40705141243).
- Additional hardening added tests and checks for spoofed founder escrow, external proceeds balances and false funding/activation claims. See [PR #129 checks](https://github.com/tgibbsz32/forgecoin/pull/129/checks) for **final commit** status. Do not claim final successful validation without seeing these complete.
- CI is a *unit/static test*, not an escrow audit, a legal opinion or a financial balance attestation.

## What did NOT happen

- **No Solana mainnet mint, supply or existing holder proven**; no replacement token created.
- **No treasury or wallet address inserted**, and no multisig controller or beneficiary signed a transaction.
- **No founder tokens issued, transferred or vested on-chain**. The immediate 15M release is the *intended unlocked bucket*, not a past event.
- **No mFRG/FRG swap, staking reward program, liquidity pool, sale quote, checkout or fund collection** has been activated.
- No FRG core consensus, PoW, tail emission or mainnet daemon modified.

## NEXT — STEP 11: authenticated mint ownership and production custody design

1. Obtain **the actual mFRG mainnet mint address from owner-controlled issuance evidence**, plus the creation transaction signature and trusted independent Solana mainnet RPC/explorer evidence. Do not guess based on ticker/logo or conflate devnet and mainnet.
2. Verify token program, six decimals, current raw mint supply (target 500M), mint/freeze authorities, current holder balances and whether mint authority has been revoked. If irrevocably fixed below 500M, **stop rather than silently minting a new token**; propose an explicit, disclosed migration/alternative decision.
3. Obtain **approved public keys only** for founder wallet and independent multisig signer participants; never request seeds, mnemonic phrases, private keys or wallet files.
4. Specify audited custody, treasury token accounts and a real vesting program with **15M deferred founder escrowed** and strictly enforced monthly UTC schedule. Independently verify funded balances and ownership; publish transparent related-party disclosure.
5. Keep the existing disabled sale backend at **5M first-pilot ceiling** and the 50M lifetime inventory separate. Complete tax, legal, security/consumer protection reviews and supply custody proof before any sale contracts or staking activation.

**Handoff rule:** At the end of each further implementation stage, commit a numbered `docs/handoffs/MFRG_500M_STEP_NN_...md` with exact PR, test result, changes, blocked or unperformed actions and next stage.
