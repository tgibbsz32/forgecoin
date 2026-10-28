# miniFORGE (mFRG) — STEP 11 handoff: two-source mint evidence checks

**Date:** October 28, 2026
**Repository:** tgibbsz32/forgecoin
**Review PR:** [#130](https://github.com/tgibbsz32/forgecoin/pull/130)
**Status:** Offline comparison tooling and first CI tests successful. No actual mainnet mFRG mint/holder inventory has been authenticated; no on-chain financial action taken.

## Objective

Continue [Step 10](MFRG_500M_STEP_10_TREASURY_VESTING_PREFLIGHT_2026-10-28.md) by improving evidence quality before any nine-account treasury funding or founder vesting. Step 10's nine-account template is **not an issued-token registry**. The genuine owner-controlled Solana mainnet mFRG mint, signer authorities and balances are still unknown in GitHub. This step cannot responsibly assume the token is missing, minted or under the founder's control.

## Source and implementation

- tools/reconcile_mfrg_mint_snapshots.py — compares two saved, separately claimed SPL mint responses, validates source labels as distinct HTTPS hostnames, and checks the same program, 6 decimals, raw minted supply, mint authority, freeze authority and policy classification. Rejects duplicate evidence documents, inconsistent token data and excessive slot separation. Reports evidence SHA-256 digests.
- tools/test_reconcile_mfrg_mint_snapshots.py — **16 synthetic offline test methods**: mismatched raw supply, mint/freeze authorities, wrong program/mint, devnet address, invalid or credential-bearing RPC labels, stale slots, identical evidence and CLI failures. No live RPC or real user wallet required.
- docs/MFRG_DUAL_SOURCE_MINT_VERIFICATION.md — owner-controlled mint identity evidence checklist, Windows PowerShell **read-only** example for two genuinely independent Solana mainnet RPC providers, interpretation of mutually agreeing snapshots, and subsequent account-ownership proof requirements.
- docs/index.md and docs/MFRG_SOLANA_MINT_VERIFICATION.md — links to the new evidence procedure.
- .github/workflows/mfrg-dual-source-mint.yml — dedicated read-only CI running the dual-source tests and existing snapshot, treasury, founder vesting and disabled-sale policy checks.

## CI evidence / branch state

- Initial PR head db35d17d3e7b02cd6bce96f822ecfd908adeecb0 passed [dual-source synthetic tests (run 40707133840)](https://github.com/tgibbsz32/forgecoin/actions/runs/40707133840) and [existing mainnet mint preflight (run 40707133423)](https://github.com/tgibbsz32/forgecoin/actions/runs/40707133423).
- This handoff file is written after the initial passing tests; **review latest PR checks before merge**. Do not claim passing final CI until GitHub returns success for the exact final head commit.
- A successful test means internally consistent **synthetic** data and disabled production flags, **not** mainnet attestation, wallet ownership, valid RPC provenance, token audit or financial deployment.

## Tokenomics invariant (unchanged)

| Budget | Tokens |
| --- | ---: |
| Proposed mFRG fixed lifetime supply | 500,000,000 |
| Lifetime fundraising reserve, *not current sale supply* | 50,000,000 |
| **Initial, still disabled, pilot checkout cap** | **5,000,000** |
| Operations | 100,000,000 |
| Ecosystem | 100,000,000 |
| Finite staking/participation reserve | 85,000,000 |
| Liquidity | 60,000,000 |
| Engineering/security | 65,000,000 |
| **Founder unrestricted at actual launch** | **15,000,000 (3%)** |
| **Team-labeled, same founder beneficial owner** | **15,000,000 (3%)**, vesting 625,000/month at ends of months 13–36 |
| Emergency | 10,000,000 |

All nine mutually exclusive budget categories sum to 500M. **Total founder beneficial ownership is 30M (6%)**. "Unlocked at launch" is a contractual target, not proof tokens have already transferred. The vesting schedule requires an actual future launch timestamp, fully funded vault and independently audited program; currently none is confirmed.

Native FRG remains a separate RandomX-mined chain, with no changes to core consensus/issuance in this step.

## What is explicitly NOT verified or authorized

- No owner-authenticated actual Solana mainnet mFRG mint address.
- No real mainnet supply or mint/freeze authority verified from trusted live evidence, and no existing holder inventory.
- The two source hostname labels and JSON responses are **untrusted inputs**; the script always returns rpc_provenance_authenticated=false, independent_network_sources_proven=false, mint_ownership_proven=false, and sale_or_issuance_authorized=false, even for agreeing files.
- No token vault, 15M unrestricted founder transfer, 15M deferred founder escrow, multisig provisioning, LP, staking, payment settlement, mint operation or change of authority.
- No checkout or live sale; public sale/payment/quote/fulfillment flags remain false.

## Next stage — STEP 12: owner-authenticated mint, then read-only token-account inventory

1. Obtain the actual existing mainnet mFRG mint public key and **mint creation signature** from the owner's authorized deployment records or wallet history. Use independent mainnet explorer and provider verification, not ticker search. Do not disclose private keys or seed phrases.
2. Capture finalized read-only Solana mainnet mint responses from two genuinely independent providers and record their provenance outside GitHub. Reconcile via the Step 11 parser. Disagreement or missing authority fields blocks progression.
3. Query a **complete** set of actual SPL token accounts/holders from independently authenticated chain state, including delegated accounts, vesting contracts, liquidity vaults and outside holders. Distinguish mint supply, circulating supply, locked balances, authority ownership and project beneficial custody. Read-only cross-check the balances against the 500M target without double counting.
4. If the existing mint is permanently fixed below 500M, do not try to mint more; obtain an explicit owner decision on an appropriately disclosed migration or alternate tokenomics.
5. Once authentic mainnet data and actual signers are verified, specify a separate production treasury/vesting implementation with independent security and legal review. Do **not** enable the old sale PR #122 or lift the initial 5M pilot cap.

At the end of each subsequent step, commit another numbered handoff listing exact files, PR, tested commit and what did **not** occur.
