# mFRG 500M — Mainnet pre-deployment readiness phase handoff

**Date:** 2026-10-28. **Repository:** tgibbsz32/forgecoin.
**Phase status:** Policy and synthetic readiness checks implemented; **PRODUCTION DEPLOYMENT NOT APPROVED**.

## Architectural correction
The owner confirmed that mFRG has **not yet been created on Solana mainnet**. Prior Steps 17–34 built offline proof and opt-in read-only verification; the absence of an initialization transaction for a mint that does not yet exist is expected. Those validators become relevant after an explicitly approved deployment. It is incorrect to characterize the non-existent current production mint as missing audit evidence of an already completed deployment.

## Deliverables
- `tools/mfrg_predeployment_preflight.py`: fail-closed, non-transactional audit of the complete existing `apps/desktop/config/miniFORGE.mainnet.plan.json` against the planned 500M supply with six decimals, standard SPL program, nine exact allocations, schedules, 30M same-founder beneficial interest, 24 deferred vesting unlocks, 50M lifetime fundraising / 5M pilot and disabled live operations.
- `tools/test_mfrg_predeployment_preflight.py`: synthetic adversarial checks of supply, schedule, duplicate categories, vesting and unsafe launch flag changes.
- GitHub workflow that runs the test suite and audits the current planning config.

## Explicit deployment acceptance gates
1. Decide and document mainnet deployment signer custody, fee payer and secure hardware/offline signing process; provision accounts and independent multisig governance with independently verified public keys. Never commit secrets.
2. Review standard SPL mint design and exact instructions; use the intended 500,000,000 supply at six decimals, reconcile the nine actual holder accounts and mint authority, then permanently revoke mint authority only in the formally approved execution plan after successful supply reconciliation.
3. Prepare transaction simulations and rollback/failure contingencies, fee/rent budget, reproducible environment, independent security audit and legal/governance authorization.
4. Require explicit final owner approval for actual mainnet creation. Never infer authorization from passing CI or planning flags.
5. **After** deployment, record real mint public key, authentic initializing transaction signatures, finalized account inventory, treasury control and externally anchored verification evidence; then exercise the existing opt-in read-only validators.
6. Presale and staking stay separate release gates. No SOL/USDC checkout, liquidity provision, token distribution, wallet signer integration or FRG mainnet activation is implied.

## Current economic plan
mFRG: 500,000,000 proposed fixed-supply tokens, six decimals. Nine allocations: fundraising 50M (5M pilot), operations 100M, ecosystem 100M, staking rewards 85M, liquidity 60M, engineering/security 65M, founder immediate 15M, founder-beneficial team-labeled vesting 15M (625,000 each month 13–36), emergency 10M. Founder combined 30M / 6%. Native FRG RandomX network remains separate; no FRG consensus or emission changes.

## What did NOT happen
No Solana keys generated, mainnet accounts created, funds sent, tokens minted, mint authority changed, sale activated, production signer provisioned or security audit completed. This phase is **predeployment policy-validation groundwork**; the next major phase is secure transaction-plan construction and independent review before deployment.
