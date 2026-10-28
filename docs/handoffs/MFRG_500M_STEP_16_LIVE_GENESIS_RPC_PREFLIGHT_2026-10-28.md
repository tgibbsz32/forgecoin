# miniFORGE 500M — STEP 16 handoff: read-only two-RPC Solana genesis and mint transaction preflight

**Date:** October 28, 2026
**Repository:** `tgibbsz32/forgecoin`
**Review PR:** [#135 — opt-in live mainnet genesis RPC safety gate](https://github.com/tgibbsz32/forgecoin/pull/135)
**Status:** New code, documentation and mock tests implemented. Real mainnet mFRG identity still not authenticated and all financial functionality remains disabled. Review CI on the final commit before merge.

## Scope and why this was Step 16

Upon resuming after [Step 14](MFRG_500M_STEP_14_MULTISIG_PDA_CUSTODY_PREFLIGHT_2026-10-28.md), the GitHub repository had already advanced: [Step 15 / PR #134](https://github.com/tgibbsz32/forgecoin/pull/134) was merged at `85d9f08ec9a3df94808be247545faa4ade63e91c`, providing offline SPL `initializeMint`/`initializeMint2` transaction parsing. **Step 15 was not duplicated.** This step adds the next safe capability: explicit operator-invoked, **read-only HTTPS queries** to actual independent Solana RPC endpoints, pinning the known mainnet genesis hash and cross-checking the mint and initialization transaction responses.

The user's actual existing mainnet mFRG mint address and creation/initialization signature **were not found in the repository records**, so the live user-specific RPC check **was not run**. A null planning mint address does **not** prove the asset does or does not exist.

## Files added and modified

1. **`tools/read_mfrg_mainnet_provenance.py`** — standard-library CLI that, only when invoked by the operator with a genuine existing mainnet mint public key and a previously existing SPL initialize transaction signature, makes **six read-only calls**: `getGenesisHash`, `getAccountInfo(jsonParsed,finalized)`, and `getTransaction(jsonParsed,finalized)` for **each of two distinct operator-selected HTTPS origins**. Requires exact canonical Mainnet Beta genesis `5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d`, consistent SPL mint, six decimals, raw supply and mint/freeze authorities and consistent successful initialization instructions. HTTP 200 only; redirects not followed; TLS hostname validation; no credentials in URL; private/local IP literals rejected; 12-second request timeout and 2 MB response limit.
2. **`tools/test_read_mfrg_mainnet_provenance.py`** — **15 synthetic unit tests**, with an injected fake RPC transport that never contacts the internet. Tests correct genesis, wrong devnet genesis, invalid mint/signature, mismatched supply, malformed transaction, missing initialization, same-host providers, dangerous URLs, bad RPC responses and repeat identical account snapshots.
3. **`docs/MFRG_LIVE_MAINNET_PROVENANCE.md`** — instructions for the exact read-only command, warnings on RPC limits and trust boundaries and preservation of blocked launch state.
4. **`.github/workflows/mfrg-live-mainnet-rpc.yml`** — synthetic tests plus existing Step 15 initialization, Step 14 multisig/PDA, lifetime policy and founder vesting safeguards.
5. **`docs/index.md`** and **`docs/MFRG_MINT_INITIALIZATION_EVIDENCE.md`** — links to the mainnet genesis provenance preflight.
6. This **numbered Step 16 handoff**.

## Tests and security fix

The initial [PR CI #40720804281](https://github.com/tgibbsz32/forgecoin/actions/runs/40720804281) identified **four failed test cases** because the URL validator's `except ValueError` accidentally caught its own `LiveReadError`, allowing *private IP literals* such as 127.0.0.1, 10.1.2.3, 169.254.169.254 and 192.168.1.1 to pass validation. The code was corrected in commit **`5152205475dfa4a5e231eca0e9d6369ec2a795a0`**, separating hostname parsing from the private-address rejection, so local/private IP literals are now rejected. Recheck all workflow results on **the final handoff-containing head** before merging. The first CI failure is disclosed rather than represented as a fully successful initial run.

The RPC transport itself is also injectable in tests and never called during synthetic CI. No live Solana data is embedded in fixtures.

## Honest verification boundary

A successful future execution may mean that **two distinct TLS-connected HTTPS hosts reported the known genesis hash and gave mutually consistent account and initialization responses**. This does NOT independently prove:
- That two RPC hostnames are actually unrelated providers, that RPC responses cannot be fabricated, or that the Solana transaction's cryptographic signature was independently verified.
- That the actual mint belongs to the ForgeCoin issuer, that the current owner authority is authorized, that nine treasury vaults have been funded, or that founder and signer beneficial ownership is independently proven.
- That on-chain supply already equals the 500M target, that funds are liquid, or that governance, vesting, staking or a token sale is live.
- That an unavailable `getTransaction` record proves a token was never created; archive RPC history limitations are possible.

**All issuer/beneficial identity, financial, and sale/issuance authorization flags remain false.** The HTTPS connection, genesis check and parsed consistency are technical preflight evidence only. No wallet secret is read or requested.

## Economic and native-chain rules preserved

| Proposed mFRG budget | Tokens |
| --- | ---: |
| Lifetime fundraising budget | 50M (of which **only 5M initial pilot**, still disabled) |
| Operations | 100M |
| Ecosystem | 100M |
| Finite participation/staking | 85M |
| Liquidity | 60M |
| Engineering and security | 65M |
| Founder immediate, unrestricted only if actually distributed at a valid launch | **15M (3%)** |
| Same-founder beneficial, team-labeled deferred, 625k monthly ends of months 13–36 | **15M (3%)** |
| Emergency | 10M |
| **Total intended mFRG supply** | **500M** |

The **same founder receives the entire 30M (6%) beneficial allocation**. The 50M long-run fundraising reserve is **not** permission to activate a 50M sale or expand the 5M first pilot. Native FRG is a separate RandomX-mined asset; no native mining/consensus change occurred.

## NEXT — Step 17: use authenticated mint records or explicitly preserve deployment block

1. Obtain from the owner the **actual existing** mainnet mFRG mint public address and its successful initialization transaction signature, without requesting any private keys or wallet recovery phrases.
2. After separately validating the source records, run `python3 tools/read_mfrg_mainnet_provenance.py --mint <actual_public_address> --signature <existing_signature> --rpc-one <approved_https_origin> --rpc-two <different_approved_https_origin>`. Use genuine independent providers, and an archive RPC if older transactions are unavailable.
3. Independently inspect a trusted mainnet explorer/verified wallet history, then reconcile current mint supply and all real token holder accounts (Steps 11–14), confirm multisig signer independence and founder beneficial custody.
4. If authenticated mint/transaction records are still missing, **keep mint, treasury, staking, sale, liquidity and vesting deployment blocked**. Do not silently create a new token or claim a 500M issued quantity; safely continue only with static/read-only testable preparation.
5. Before any on-chain transfer/authority changes, secure separate explicit owner authorization, appropriate security/legal reviews and a new handoff.

**Continuation convention:** Each future “continue” completes one reviewable stage, checks CI, commits a numbered handoff, and stops. No deployment or transfers without genuinely verified mint/custody and explicit authorization.
