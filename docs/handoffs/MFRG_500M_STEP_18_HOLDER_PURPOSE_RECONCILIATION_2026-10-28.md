# miniFORGE 500M — STEP 18 handoff: offline holder-to-purpose reconciliation

**Date:** 2026-10-28. **Repository:** tgibbsz32/forgecoin. **Status:** Synthetic-only, pre-mainnet verification hold. Review the Step 18 PR and final GitHub CI separately; this document does not assert that the PR merged.

## Prior step
[Step 17 PR #137](https://github.com/tgibbsz32/forgecoin/pull/137) is merged. It added opt-in, two-RPC Solana mainnet genesis/mint/holder scans but DID NOT establish a genuine owner-authenticated existing mainnet mFRG mint, token holder identity, or true account completeness.

## Completed implementation
- Added `tools/reconcile_mfrg_holder_purposes.py`: a **fully offline JSON accounting and claimed-attestation gate**. It requires schema 1, mainnet-beta, original SPL Token Program, six decimals, a non-devnet mint-shaped identifier, an initialization-signature-shaped identifier, nonduplicate token accounts, nonnegative integer atomic balances, conservation against reported minted supply, maximum 500M supply, and caps for nine fixed intended budgets. Purpose-assigned balances require *explicit externally verified* owner, governance, and beneficial-owner boolean attestations; non-project balances are classified `unassigned`.
- Added `tools/test_reconcile_mfrg_holder_purposes.py`: 16 synthetic no-network cases; intentionally fake addresses and fake flags only.
- Added `.github/workflows/mfrg-holder-purpose-reconciliation.yml`: new synthetic tests plus Step 17 regression tests.
- This numbered handoff.
- The validator does **not** fetch or verify signatures, attestation validity, beneficial ownership, RPC responses or chain history. It NEVER asserts that even all-nine-full category totals represent genuine treasury holdings, and emits `sale_authorized: false` and `treasury_release_authorized: false` on every successful result. Attestation booleans are **operator declarations**, not cryptographic checks. Do not publish an accounting PASS as a release approval.

## Operator process — blocked on real evidence
1. Acquire the true mainnet mint and mint-initialization signature from **owner-authenticated public deployment evidence**. Do not substitute devnet mint `9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw`.
2. Run Step 17's read-only two-RPC checker, corroborate with independent trusted explorer/history, and record slot, source, program controls and token-account owner details.
3. Prepare a local JSON manifest with keys `schema_version`, `network`, `token_program`, `decimals`, `mint`, `initialization_signature`, `mint_supply_atomic`, and `accounts`. Each account has `token_account`, `amount_atomic`, `purpose` (one of the nine exact budget keys or `unassigned`), and, for assigned project funds only, `owner_attestation_verified`, `governance_authorization_verified`, `beneficial_owner_verified` (all true after independent external review). No mnemonic, private key or identifying KYC evidence belongs in the JSON.
4. Run `python tools/reconcile_mfrg_holder_purposes.py path/to/local-manifest.json` and preserve evidence pointers separately. This is **accounting only**; externally review actual attestations. Unassigned represents non-project or unattributed tokens, **not** proof of their ownership.
5. Do not enable issuance, pilot sale, fund movements, token conversion, multisig deployment, or founder vesting funding through this tool. A 500M intended budget is not proof of a 500M minted supply.

## Fixed nine budgets (tokens, not atomic units)
Fundraising 50M lifetime / 5M initial pilot; operations 100M; ecosystem 100M; finite staking rewards 85M; liquidity 60M; engineering/security 65M; founder immediate 15M; founder vesting 15M at proposed 625k monthly ends of months 13–36; emergency 10M. Same founder benefits from both founder allocations: 30M/6%.

## NEXT — STEP 19
Require independently verifiable signed ownership/governance attestations (not boolean operator declarations), bind them to exact token-account public keys and purpose budgets, and compare against externally corroborated mint/token snapshots. First collect authenticated real deployment identifiers. If unavailable, remain BLOCKED. Only propose code/tests/docs without claiming operational deployment. Review and merge the PR only after GitHub CI succeeds.
