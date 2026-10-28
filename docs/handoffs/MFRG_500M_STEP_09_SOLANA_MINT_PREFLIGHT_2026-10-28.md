# miniFORGE 500M — STEP 09 handoff: read-only Solana mint preflight and segregated treasury gates

**Date:** October 28, 2026
**Repository:** `tgibbsz32/forgecoin`
**Working PR:** [#128 — verify Solana mint snapshots safely](https://github.com/tgibbsz32/forgecoin/pull/128)
**Validation:** [GitHub Actions run 40703194924](https://github.com/tgibbsz32/forgecoin/actions/runs/40703194924) — **completed successfully** on `d761bd9bf68d5cb7f0363db4687efdffcf876e32`.
**State:** Offline mint snapshot parser, synthetic tests and technical custody specification complete. No actual mainnet mFRG mint independently verified.

## Actual project evidence

1. On repository `main`, the current `apps/desktop/config/miniFORGE.mainnet.plan.json` is **non-transactional planning data** targeting **500,000,000 mFRG (6 decimals)**. Its `network_mint_address` is `null`, mint authority `unverified`, all nine intended owner/token account addresses `null`, and issuer/sale/staking/liquidity authorization flags `false`. This is **not** a ledger record.
2. The historically recorded test mint `9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw` was **devnet-only**, not an official mainnet mFRG identifier.
3. The October 27 reported 0 SOL fee-payer balance is **historical**, not a current verified observation.
4. The user previously discussed creating the SPL asset, but this step found **no actual mainnet mint address, issuance transaction signature, authenticated supply snapshot or mainnet authority record** that establishes minting. **Do not assert that the mint does or does not currently exist.** The user's mint can only be identified through authenticated owner deployment evidence, not a name/ticker search.
5. Step 08 merged a strictly offline sale-test backend via [PR #127](https://github.com/tgibbsz32/forgecoin/pull/127); lifetime fundraising 50M does **not** enlarge the 5M initial pilot. No sale is active.

## Code and document deliverables

- `tools/verify_mfrg_mint_snapshot.py`: **offline, read-only** command accepting a caller-supplied mint address and Solana `getAccountInfo` JSON. Rejects a wrong program, wrong mint type, invalid base58 key, wrong 6-decimal metadata, absent/malformed `mintAuthority` or `freezeAuthority`, negative/noninteger supply, raw >500M policy cap, missing observation slot or empty account. Refuses the old devnet mint. Returns a constrained classification, explicitly `independently_authenticated_mainnet: false` and `sale_or_issuance_authorized: false`.
- `tools/test_verify_mfrg_mint_snapshot.py`: **15 synthetic scenario methods**, including fixed-target vs permanently fixed-below-target, active authority cases, invalid account shapes, wrong mint ID, freeze authority, supply overflow and Windows PowerShell UTF-8 BOM behavior. All addresses are synthetic fixtures, NOT actual project mint evidence.
- `docs/MFRG_SOLANA_MINT_VERIFICATION.md`: PowerShell step-by-step guide to obtain the actual authorized mainnet mint address and an independently sourced read-only RPC snapshot; cautions that a JSON file alone cannot authenticate its origin.
- `docs/MFRG_TREASURY_VESTING_GATES.md`: nine earmarked custody accounts, independent USDC/SOL proceeds ledger, multisig policy, no double counting, founder immediate/deferred beneficial-owner disclosures, testable calendar-month vesting specification, staking/LP and legal gates.
- `.github/workflows/mfrg-mint-preflight.yml`: CI executes the parser's synthetic test suite, existing 500M accounting guardrails and the offline 5M pilot backend tests.

## Supply and vesting requirements unchanged

| Asset/budget | Amount |
| --- | ---: |
| Intended fixed SPL total | 500,000,000 mFRG |
| Lifetime proposed crypto-denominated fundraising | 50,000,000 mFRG |
| Initially authorized pilot maximum | 5,000,000 mFRG |
| **Founder unrestricted at issuance/launch** | **15,000,000 mFRG (3%)** |
| **Founder-beneficial team-labeled deferred allocation** | **15,000,000 mFRG (3%)**, with 625,000 unlocks monthly in months 13–36 |
| Founder total beneficial share | **30,000,000 mFRG (6%)** |
| Additional allocations | 100M operations; 100M ecosystem; 85M staking rewards; 60M liquidity; 65M engineering; 10M emergency |

Native FRG remains a separate RandomX-mined asset with its own consensus and tail emission; nothing in this step modified it.

## Verified tests and limits

- [CI run #40703194924](https://github.com/tgibbsz32/forgecoin/actions/runs/40703194924) **completed successfully** before this documentation-only handoff commit. It ran:
  - `python3 tools/test_verify_mfrg_mint_snapshot.py` (synthetic).
  - `python3 tools/test_mfrg_policy.py` (inert configuration and site sale-disabled guardrails).
  - `python3 apps/sale/tests/test_sale.py` (offline pilot/receipt/anti-replay accounting).
- Offline parser results **do not** constitute independent Solana mainnet RPC authentication, key ownership proof, completed treasury funding, an audit, legal authorization or supply attestation. No actual token account address or mint address has been asserted.
- No spending private key, seed, network signature, SOL, USDC or mFRG was accessed or moved.
- All production sale, staking, minting and liquidity activation guards remain false.
- The earlier [PR #122](https://github.com/tgibbsz32/forgecoin/pull/122) still contains obsolete site/economic diffs and separate development-only Rust escrow; do not merge as-is.

## NEXT — STEP 10: authenticated mint and founder treasury readiness

1. Obtain the **actual owner-authorized mFRG mainnet mint address** from real issuance records, plus a Solana transaction signature or trusted Explorer record. Do not confuse the Solana USDC address with mFRG or accept a token name search as proof.
2. Collect `getAccountInfo` `jsonParsed` from an independently verified Solana **mainnet** RPC and cross-check with a second independent source. Feed saved JSON to the new offline script using the verified mint address. Independently authenticate RPC origin and slot.
3. Depending on authority state, reconcile minted supply (target 500M), revoke mint authority only with approved signer control and after full audit, or if fixed below target evaluate a transparent migration instead of claiming further issuance possible.
4. Obtain project approval for the actual founder beneficiary address, multisig signers and 9 custody account addresses. **No escrow contract is built yet**, no founder 15M liquid tranche or vesting tranche has been transferred, and no launch date has been selected.
5. Specify and independently audit a custody/vesting contract with non-revocable **15M deferred founder** in 24 monthly 625k installments, months 13–36 from explicit UTC launch date, with owner/upgrade controls understood.
6. Keep all initial sale checkout and 5M pilot contract deployment on hold until actual mint, custody, funding, legal and security gates pass.

**Step handoff convention:** At the end of every development step, commit a new `docs/handoffs/MFRG_500M_STEP_NN_...md` with exact PR, tested SHA, successful checks, what did not happen, and the next action.
