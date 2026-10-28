# miniFORGE 500M — STEP 19 handoff: Ed25519-signed offline claim gate

**Date:** 2026-10-28. **Repo:** tgibbsz32/forgecoin. **PR:** Step 19 development branch; verify CI and final merge separately.

## Completed
- `tools/verify_mfrg_signed_attestations.py`: verifies detached Ed25519 signatures over domain-separated, canonical JSON claims with exact version, network, mint, mint-initialization signature, token-account address, purpose, atomic amount and signer role.
- External operator-supplied trust policy binds signer IDs to public keys and distinct owner/governance roles; duplicate role attestations, missing roles, tampering, incorrect account balances and conflicting purposes block.
- Bridges into Step 18 offline conservation and nine-category budget logic; discards Step 18 owner/governance assertion booleans and derives those two from verified signatures.
- Fifteen synthetic tests, a dedicated CI workflow and Step 18 regression cases.

## Security limitations
**This checks only whether authorized-in-policy signing keys signed specific offline claims**. It does NOT authenticate those keys as project officials, prove Solana token-account control, cryptographically establish beneficial ownership, verify live RPC mint data, prove custody or allow treasury releases. External beneficial-owner review remains an independent gate, and a true boolean in local JSON is NOT independently verified by this tool. The manifest must be tied to an independently corroborated Step 17 mainnet snapshot. The owner-supplied trust policy must be verified via an out-of-band governance channel; a trust policy prepared by an attacker can make attacker signatures pass.

No real mainnet mFRG mint public key or initialize transaction has been independently authenticated in repository evidence. No actual mint, sale, payment, fund transfer, vault, multisig, vesting, or staking operation performed. Intended 500M mFRG / six decimals, nine budgets, 50M lifetime sale allocation with 5M pilot, and same-founder beneficial 30M/6% unchanged.

## Offline operator usage
`python3 -m pip install 'cryptography>=43,<47'`
`python3 tools/verify_mfrg_signed_attestations.py manifest.json verified-signers.json`

`manifest.json` extends Step 18's schema with `signed_attestations` containing `signer_id`, `claim`, and `signature_base64`. Each assigned token account requires two signed claims: owner and governance, each bound to the exact account purpose and atomic balance. `verified-signers.json` contains `trusted_signers` mapping IDs to `role` and `public_key_base64` (raw 32-byte Ed25519 public key). Signatures are base64-encoded raw 64-byte Ed25519 signatures of `b"FORGECOIN-MFRG-PURPOSE-ATTESTATION-V1\\n" + canonical JSON`, where canonical JSON is sorted keys, ASCII escaping and compact separators. Never place signing seeds or private keys in these files.

## NEXT — STEP 20
Require independent authentication of the signer trust registry and signed Solana account-control challenges, plus external snapshot provenance cross-checks. Refuse release if mint and initialization signature cannot be established. Complete CI and merge review before proceeding.
