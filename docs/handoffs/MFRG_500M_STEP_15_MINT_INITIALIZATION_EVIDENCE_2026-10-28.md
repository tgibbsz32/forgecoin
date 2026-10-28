# miniFORGE 500M — STEP 15 handoff: offline SPL mint initialization evidence

**Date:** October 28, 2026
**Repository:** `tgibbsz32/forgecoin`
**PR:** [#134 — cross-check SPL mint initialization transaction evidence](https://github.com/tgibbsz32/forgecoin/pull/134)
**Status:** Offline evidence parser and synthetic tests implemented; no authenticated mainnet mint, transaction, custody or financial action established.

## Reason for this step

[Step 14](MFRG_500M_STEP_14_MULTISIG_PDA_CUSTODY_PREFLIGHT_2026-10-28.md) added tests for SPL multisig authority structure and explicit PDA verification blockers. The next production-readiness blocker remains **the lack of a genuine independently authenticated Solana mainnet mFRG mint public key and initialization transaction signature**.

Before writing a mainnet config or deploying accounts, the project needs an auditable record linking an authorized mint address to an initial **successful SPL Token Program initializeMint/initializeMint2 transaction**, and later the actually deployed mint account. GitHub searches in this step found only planning documentation, references and safety code; `apps/desktop/config/miniFORGE.mainnet.plan.json` still has `network_mint_address: null` and mint authority status `unverified`. **This does not prove that no real mint exists, only that it was not authenticated in the consulted repository records.** The historical devnet mint must not be relabeled as mainnet.

## Completed files

1. `tools/verify_mfrg_mint_initialization.py`: **offline-only**, read-only cross-check of two caller-supplied `getTransaction(encoding=jsonParsed)` responses and a later `getAccountInfo(encoding=jsonParsed)` mint snapshot. Requires a valid 64-byte Solana base58 signature string, primary signature match, successful transaction status (`meta.err=null`), parsed writable mint key, exactly one original SPL Token Program `initializeMint` or `initializeMint2` instruction (including CPI), decimals 6, and consistent initialization authority, slot and mint identity across both responses. Requires the mint to exist in the later supplied snapshot with correct program owner, mint metadata and no supply beyond the **proposed** 500M cap.
2. `tools/test_verify_mfrg_mint_initialization.py`: **21 synthetic test methods**, including valid `initializeMint`/`initializeMint2`, inner-instruction handling, failed transaction, wrong mint or program, invalid decimals, mismatched authorities/slots, revocation of current authority after initialization, missing/altered signature, non-writable mint, duplicate initialization, missing response, devnet mint and Windows BOM compatibility. All fixtures are fabricated; synthetic 64-zero-byte signature is not real cryptographic proof.
3. `docs/MFRG_MINT_INITIALIZATION_EVIDENCE.md`: step-by-step read-only PowerShell evidence capture from two independently selected Solana mainnet RPC providers, provenance limits and runbook. `result:null` may mean unavailable transaction history; it is **not evidence that the mint does not exist**.
4. `.github/workflows/mfrg-mint-initialization.yml`: runs initialization tests, previous dual-source mint comparison, multisig/PDA safety, 500M policy/disabled pilot and founder vesting regression tests with read-only GitHub permissions.
5. `docs/index.md` and `docs/MFRG_SOLANA_MINT_VERIFICATION.md`: links to Step 15 procedure.
6. This permanent numbered `STEP_15` handoff.

## Test evidence and limitations

On initial PR head `6dba84220e333c3c866fb637c190402d3963d37a`:
- [Step 15 initialization CI #40717179152](https://github.com/tgibbsz32/forgecoin/actions/runs/40717179152): **success**.
- [Step 14 multisig/PDA regression #40717178885](https://github.com/tgibbsz32/forgecoin/actions/runs/40717178885): **success**.
- [Step 13 owner-purpose consent #40717178974](https://github.com/tgibbsz32/forgecoin/actions/runs/40717178974): **success**.
- [Step 12 inventory #40717178873](https://github.com/tgibbsz32/forgecoin/actions/runs/40717178873): **success**.
- [Step 9 mint preflight #40717178863](https://github.com/tgibbsz32/forgecoin/actions/runs/40717178863): was still running when initially checked; check final result on [PR #134](https://github.com/tgibbsz32/forgecoin/pull/134/checks).
- This handoff commit follows initial CI. **Confirm exact final head checks and merge state before declaring Step 15 fully merged.**

**Every tool-positive response explicitly reports** `initialized_mint_on_mainnet_authenticated=false`, `independent_rpc_provenance_verified=false`, `transaction_signature_cryptographically_verified=false`, `project_issuer_identity_verified=false`, `mint_and_holder_custody_verified=false` and `sale_or_issuance_authorized=false`. Parsed transaction JSON is untrusted input. Merely matching two labelled sources cannot independently establish signer authorization, verified transaction wire bytes or chain provenance.

## Invariant economic plan (not minted-proof)

| Budget | Intended mFRG |
| --- | ---: |
| Fundraising lifetime reserve (initial pilot **5M subset only**) | 50,000,000 |
| Operations | 100,000,000 |
| Ecosystem | 100,000,000 |
| Finite staking and participation inventory | 85,000,000 |
| Liquidity inventory | 60,000,000 |
| Engineering/security | 65,000,000 |
| Founder immediately unrestricted **only once validly transferred** | 15,000,000 (3%) |
| Team-labeled deferred, **same founder beneficial owner** | 15,000,000 (3%) |
| Emergency | 10,000,000 |
| **Nine total categories** | **500,000,000** |

Founder total beneficial share remains **30M/6%**. Deferred 15M is planned to vest **24 × 625,000 mFRG** at ends of calendar months **13–36**, beginning after 12 full months from a future verified UTC launch timestamp. No funded contract exists in this step.

The native FRG RandomX-based chain remains wholly separate.

## Explicitly unperformed

- No mainnet mFRG mint created or existing mainnet mint independently identified/authenticated.
- No on-chain issuance, mint/freeze authority change, actual supply, public holder inventory, independent signer custody or program deployment attested.
- No nine treasuries funded, no multisig or PDA created, no founder vesting or unrestricted grant transferred.
- No USDC/SOL payment, live swap, sale, LP or staking program, token quotation or website checkout enabled.
- No FRG consensus or tail emission changed.

## NEXT — Step 16 authenticated holder and custody readiness

**Critical external evidence required**: actual owner-authenticated existing mainnet mint public key **and its initializing transaction signature**, verified through independent mainnet RPC/explorer sources. Once supplied, verify the mint account/supply and current authorities against the historical initialization. Then compare existing token-account inventory and signer authority; do not infer project/beneficiary ownership solely from token symbols, signatures or account public keys.

If those records remain unavailable, the appropriate next step is to maintain an explicit **blocked live-deployment gate** rather than repeatedly writing hypothetical on-chain allocations. Separate legal/security/authorization approvals are required before any real mint, payment or treasury transaction.

**Continuation convention:** After each user “continue,” complete one reviewable step, run CI, record honest verification boundaries and commit numbered handoff, then stop.
