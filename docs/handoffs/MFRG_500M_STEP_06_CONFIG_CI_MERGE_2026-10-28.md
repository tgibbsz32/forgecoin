# miniFORGE 500M — STEP 06 handoff: consistency tests passed and configuration merged

**Date:** October 28, 2026
**State:** Completed; production financial functionality remains disabled.

## Version control / evidence

- **PR:** [#126 — migrate inert desktop planning config and add 500M guardrails](https://github.com/tgibbsz32/forgecoin/pull/126), merged to `main`.
- **Merged commit:** `817a74f84178af3aa2e93fb6ae413067121b61e8`.
- **CI:** [miniFORGE tokenomics policy guardrails — run 40654424880](https://github.com/tgibbsz32/forgecoin/actions/runs/40654424880) **completed successfully** against the PR commit `28df45a32e1fdcf47c2bed8284f38cf2b50b71e7`. The workflow is now installed for future relevant pull requests and `main` pushes.
- **Previous informational-document PR:** [#125](https://github.com/tgibbsz32/forgecoin/pull/125) completed successfully, with both GitHub Pages jobs successful. Review the separate [STEP 04 handoff](MFRG_500M_STEP_04_PUBLICATION_2026-10-28.md) for publication details.
- **Detailed code edit inventory / rationale:** [STEP 05](MFRG_500M_STEP_05_CONFIGURATION_MIGRATION_2026-10-28.md).

## Validated scope

The desktop planning data `apps/desktop/config/miniFORGE.mainnet.plan.json` is now schema v2, **500,000,000 mFRG target**, 6 decimals = **500,000,000,000,000 atomic units**, with nine distinct buckets totaling exactly 500M:

| Budget | mFRG |
|---|---:|
| Fundraising | 50,000,000 |
| Operations | 100,000,000 |
| Ecosystem grants | 100,000,000 |
| Staking rewards | 85,000,000 |
| Liquidity | 60,000,000 |
| Engineering/security | 65,000,000 |
| Founder — unrestricted at launch | 15,000,000 |
| Team-labeled, founder-beneficial — months 13–36 | 15,000,000 |
| Emergency | 10,000,000 |
| **Total** | **500,000,000** |

The founder owns both 3% buckets beneficially. Vesting is **625,000 × 24 months = 15M**, beginning month 13 and ending month 36. Maximum time-bucket releases and active public site status fields reconciled. The added offline Python tests and CI checked these invariants as well as the disabled sale/quote/payment/fulfillment state and the desktop wallet's **separate mainnet mint gate**.

The Windows wallet now uses non-assumptive language **“Mainnet mint unconfigured”** until a verified mint is available. The wallet continues to read a different production file with explicit `productionReady=true`; this update did not add one. No token balances or custody accounts were changed.

## Security/compliance boundaries

- **No mint address independently verified on chain in this step.** A planning file is not a ledger entry or a mint.
- No Solana transaction signed; no mint authority action, transfer, founder unlock, treasury vault creation, stake deposit, liquidity pairing or funds collection.
- All public website sales, quote and payment controls remain disabled. No fixed conversion with native FRG.
- Native FRG remains on previously documented RandomX consensus and tail-emission model, without changes.
- Automatic CI validates documented accounting and disabled flags; **it is not a cryptographic, legal or production smart-contract audit**.

## NEXT — STEP 07: older sale prototype reconciliation

[PR #122](https://github.com/tgibbsz32/forgecoin/pull/122) remains open and is based on an older mFRG supply and 5M checkout-inventory assumption. Inspect its escrow contract, integer-based quote code, backend ledger, signature/transaction receipt validation, and tests for any assumptions that conflict with the new **50M lifetime fundraising budget with initial 5M pilot**.

**Do not merge or activate sale PR #122 without a separate security, legal, treasury and mint-authority review.** Draft follow-up changes on a separate branch/PR, keep all payment/quote execution disabled and write a STEP 07 handoff of findings and verified remediations.

After this audit, the next on-chain dependency is obtaining the **actual already-created mainnet mFRG mint address** and verifying supply/authority from a trusted Solana mainnet source; do not invent the address, assume it does not exist, or create a replacement mint without a documented migration decision.
