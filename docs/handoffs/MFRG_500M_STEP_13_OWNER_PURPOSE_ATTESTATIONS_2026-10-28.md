# miniFORGE 500M — STEP 13 handoff: offline cryptographic owner-purpose consent checks

**Date:** October 28, 2026
**Repository:** `tgibbsz32/forgecoin`
**PR:** [#132 — offline owner-purpose attestations](https://github.com/tgibbsz32/forgecoin/pull/132)
**Status:** Developed, tested and reviewed on PR branch. Merge and final main CI should be checked independently before declaring complete.

## Why this was the next safe implementation step

[Step 12](MFRG_500M_STEP_12_TOKEN_ACCOUNT_INVENTORY_2026-10-28.md) reconciled *provided* SPL token-account balances, but a balance/owner public key alone cannot prove a project's signer actually authorizes the account to be associated with a proposed treasury purpose. The user still has not supplied an independently authenticated Solana **mainnet** mFRG mint public key or actual holder inventory. No mainnet mFRG mint, on-chain supply or wallet ownership has been independently established in the repository.

Step 13 therefore implements a **read-only cryptographic wallet-consent check** without introducing deployment or any live funds movement.

## New files and behavior

1. `tools/verify_mfrg_purpose_attestations.cjs` — built-in Node.js `crypto` Ed25519 detached-signature validation for an exact, domain-separated message including **mint public key, mainnet-beta, one of nine treasury purpose IDs, token account, parsed token owner authority, exact six-decimal atomic amount, unique nonce, UTC issued and expiry** (max 30 days). Checks this signed claim against a separately supplied *untrusted* `getProgramAccounts` snapshot. Does not sign or spend. Rejects signatures that are forged or altered, invalid/wrong signer, wrong mint or role, mismatched account balance/owner, over-budget purpose claims, double-counted accounts, duplicate nonces, expired consent, and delegated, frozen or close-authority-controlled custody requiring additional review.
2. `tools/test_verify_mfrg_purpose_attestations.cjs` — **24 automated tests** using ephemeral generated synthetic Ed25519 key pairs. Includes real cryptographic signature verification in unit tests but **no project keys and no network**. Tests altered roles/amounts/mints, forged signatures, blocked account states, expired consent, category limits and fail-closed CLI behavior.
3. `docs/mfrg-owner-attestation.template.json` — inert example registry, `mint:null`, `claims:[]`, all custody/production approvals false. Intentionally fails verification until local, owner-sourced evidence is available.
4. `docs/MFRG_OWNER_PURPOSE_ATTESTATIONS.md` — signature protocol, tool invocation, privacy and security boundaries, distinction of Ed25519 direct-wallet consent from beneficial ownership and **program-derived address/multisig** custody authorization.
5. `docs/index.md` — link to the operator guide.
6. `.github/workflows/mfrg-owner-purpose-attestations.yml` — Node 22 signature checks, Step 12 token-account tests, previously merged 500M allocation/sale-disabled and founder-vesting CI.
7. This numbered `STEP_13` handoff.

## Validation evidence available before handoff commit

PR head `ddebaed3f1693ad22d01a0df0e3b9e6b85792b13` passed:
- [Step 13 owner-purpose Ed25519 CI #40711041237](https://github.com/tgibbsz32/forgecoin/actions/runs/40711041237) — **success**.
- [Step 12 inventory regression CI #40711041066](https://github.com/tgibbsz32/forgecoin/actions/runs/40711041066) — **success**.

These passing tests prove only that *synthetic* signed-consent claims are checked against mock account records. **They are not real Solana mainnet ownership verification or an independent smart-contract/legal audit.** Final CI for the handoff-containing commit must be checked before merge.

## Economic and security invariants (unchanged)

- mFRG: **500,000,000 intended SPL total** at six decimals, not independently established on-chain.
- Nine separate planned allocations: 50M fundraising; 100M operations; 100M ecosystem; 85M finite staking/participation; 60M liquidity; 65M engineering/security; 15M founder immediate; 15M team-labeled deferred but **same founder beneficial owner**; 10M emergency.
- Founder **30M / 6% total beneficial control**. First 15M unrestricted only **when actually distributed at launch**; deferred 15M requires funded and audited vesting contract with **625,000 per calendar month at ends of months 13–36**.
- The fundraising budget is **50M lifetime** but **5M first-pilot maximum**; no sale is open.
- No owner address or signer has been identified as genuine; the template includes no mint, wallet public key or funded allocation.
- Direct Ed25519 proof establishes at most the possession of a private signing key behind a claimed public address for *that signed message*. It **cannot** establish beneficial ownership, legitimacy of underlying RPC snapshots, governance approval, program/PDA/multisig controls or actual token custody.
- Tool success always sets RPC/mint authentication, inventory completeness, beneficial ownership, founders verified, treasury funded and sale/issuance authorized to **false**.
- No minting, token transfer, signer delegation, multisig provisioning, founder payout, release scheduling on chain, liquidity, staking, crypto-payment acceptance, sale/quote/fulfillment activation or native FRG consensus changes were made.

## Next Step 14: independently authenticated mint and program-owner authority evidence

1. Obtain the *real* existing Solana mainnet miniFORGE mFRG mint public key and mint-creation transaction from the project's actual owner/issuer evidence (not the historic devnet mint).
2. Authenticate mainnet RPC sources and independently corroborate SPL mint account program, decimals, supply, mint/freeze authorities, and current holders using Steps 9, 11 and 12 tools.
3. For project-controlled ordinary Ed25519 wallets, seek *voluntary, separate* signed purpose consent (no private keys collected) and verify it with Step 13. **Do not label wallets as project treasury or founder beneficially owned merely because a signature matches.**
4. For proposed program-controlled escrow accounts and treasury multisigs, build an independent, security-reviewed governance/authority proof and publicly disclose actual upgrade controls, signer threshold and beneficiary identity. A PDA cannot be authenticated using an ordinary Ed25519 signature.
5. Only after actual mint, full inventory, authority/beneficial owner checks, security/legal approval and vested treasury custody designs may any on-chain action be separately approved. Keep the sale, staking and liquidity disabled and preserve the 5M initial pilot hard cap.

**Continuation rule:** Each future “continue” completes one step including checks, a reviewed PR and a numbered handoff, and stops after the step.
