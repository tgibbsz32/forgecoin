# mFRG 500M — Step 20 handoff: independently pinned registry and offline key-control challenges

**Date:** 2026-10-28; **repository:** tgibbsz32/forgecoin; **status:** synthetic-only development, NOT an on-chain release approval.

## Changes
- `tools/verify_mfrg_control_challenges.py`: builds on Steps 18–19. Trust policy must match an exact independently supplied SHA-256 digest of canonical JSON (`sort_keys=True, separators=(',', ':'), ensure_ascii=True`). **The hash must come through an authenticated independent channel, not copied from the untrusted input file.** A hash match alone does not establish that a trusted person provided it.
- Requires a signed Ed25519 challenge from the declared **single-key token-account owner public key**, bound to mainnet, exact mint, initialization signature, token account, purpose, balance, finalized snapshot slot and 256-bit hexadecimal nonce. A signature demonstrates key possession for a presented key, **not** live chain control.
- Checks one challenge per assigned account; duplicate or missing challenges, altered signatures, mismatched slots and owner keys, missing account claims and malformed nonces fail closed. This does not support PDA or SPL multisig authorities; these **must remain unverified**, not be treated as single-key custody.
- Fourteen synthetic tests, Step 19 and Step 18 regressions in a dedicated Actions workflow; zero live RPC, secret keys, token transfers or signing prompts.

## Operator command
`python3 -m pip install 'cryptography>=43,<47'`

`python3 tools/verify_mfrg_control_challenges.py manifest.json verified-signers.json snapshot-and-challenges.json --trusted-policy-sha256 INDEPENDENT_AUTHENTICATED_64_HEX_DIGEST`

JSON input schemas follow Step 19 plus:
`{"mint":"...","initialization_signature":"...","slot":123,"commitment":"finalized","account_owner_keys":{"TOKEN_ACCOUNT":"OWNER_PUBKEY"},"challenges":[{"claim":{"version":1,"network":"solana-mainnet-beta","mint":"...","initialization_signature":"...","token_account":"...","owner_key":"...","slot":123,"nonce":"64 lowercase hex","purpose":"operations","amount_atomic":1000000},"signature_base64":"64-byte-signature-encoded"}]}`.

## Unresolved blockers
The repo still lacks an independently authenticated real Solana mainnet mFRG mint, initialization signature, ownership authority list and live holder inventory. The token-account ownership mapping and slot in the local evidence JSON are merely **claims**; Step 20 does not independently fetch or verify them. Neither onchain account control, real snapshot provenance, challenge recency/replay protection across runs, governance key provenance, PDA/multisig custody, beneficial ownership, nine-budget funding nor sale authorization has been established. The program emits explicit false flags for live claims. Owner/governance signatures and `beneficial_owner_verified` are not proofs of beneficial ownership.

500M intended, six decimals, 50M lifetime fundraising with 5M initial pilot, 30M beneficial same-founder allocation, nine categories, native FRG unchanged. No mint, vault, issuance, staking, trading, payment, fund transfer or pool changes.

## NEXT — Step 21
Establish a genuine owner-authenticated mint and create transaction, corroborate holder-account keys and token balances against independently validated live chain data, and design robust nonce issuance/replay prevention. Do not elevate a synthetic offline pass to a production clearance.
